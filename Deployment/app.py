import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import base64
import scipy.optimize as optimize
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px  
import joblib
import scipy.optimize as sco
from sklearn.covariance import LedoitWolf
import warnings

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="RencanaKita", layout="wide", initial_sidebar_state="collapsed")

# --- DEFINISI BASE DIRECTORY UTAMA ---
# Mengunci root path agar selalu relatif terhadap lokasi app.py ini
BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================
# CORE ENGINE: CLASS & UTILITIES GLOBAL
# ==========================================
class BondAnalyzer:
    def __init__(self, face_value, coupon_rate, years_to_maturity, frequency=2):
        self.face_value = face_value
        self.coupon_rate = coupon_rate
        self.years_to_maturity = years_to_maturity
        self.frequency = frequency
        self.periods = years_to_maturity * frequency
        self.coupon_payment = (face_value * coupon_rate) / frequency

    def calculate_price(self, ytm):
        rate = ytm / self.frequency
        cash_flows = [self.coupon_payment] * self.periods
        cash_flows[-1] += self.face_value
        price = sum([cf / (1 + rate)**(t+1) for t, cf in enumerate(cash_flows)])
        return price

    def calculate_ytm(self, current_price):
        def objective_function(ytm_guess):
            return self.calculate_price(ytm_guess) - current_price
        try:
            ytm = optimize.newton(objective_function, self.coupon_rate)
        except:
            ytm = 0.0
        # BUG FIXED: Indentasi dikembalikan sejajar dengan try-except agar tidak me-return None
        return ytm 

    def calculate_modified_duration(self, ytm):
        rate = ytm / self.frequency
        cash_flows = [self.coupon_payment] * self.periods
        cash_flows[-1] += self.face_value
        t_values = np.arange(1, self.periods + 1)
        pv_cash_flows = [cf / (1 + rate)**t for t, cf in zip(t_values, cash_flows)]
        
        sum_pv = sum(pv_cash_flows)
        if sum_pv == 0: return 0.0
            
        macaulay_duration = sum(t * pv / sum_pv for t, pv in zip(t_values, pv_cash_flows)) / self.frequency
        mod_duration = macaulay_duration / (1 + rate)
        return mod_duration

# --- FUNGSI LOAD DATA SAHAM (UPDATED PATH MAPPING) ---
@st.cache_data
def load_stock_data(ticker):
    file_mapping = {
        'ADRO': 'ADRO_clean.csv',
        'ANTM': 'ANTM_clean.csv',
        'ASII': 'ASII_clean.csv',
        'BBCA': 'bbca_clean.csv',
        'BBNI': 'bbni_clean.csv',
        'BBRI': 'bbri_clean.csv',
        'BMRI': 'bmri_clean.csv',
        'CUAN': 'CUAN_clean.csv',
        'ICBP': 'icbp_clean.csv',
        'INCO': 'INCO_clean.csv',
        'ISAT': 'ISAT_clean.csv',
        'MEDC': 'MEDC_clean.csv',
        'MYOR': 'myor_clean.csv',
        'PTBA': 'PTBA_clean.csv',
        'TLKM': 'tlkm_clean.csv' 
    }
    
    nama_file = file_mapping.get(ticker, f"{ticker}_clean.csv")
    filepath = BASE_DIR / "Data" / nama_file # MENGGUNAKAN BASE_DIR
    
    try:
        df = pd.read_csv(filepath)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        return df
    except FileNotFoundError:
        st.error(f"🚨 File tidak ditemukan di lokasi: {filepath}")
        return pd.DataFrame()

daftar_emiten = [
    'BBCA', 'BBRI', 'BMRI', 'BBNI', 'TLKM', 
    'ASII', 'ICBP', 'CUAN', 'INCO', 'ISAT', 
    'ADRO', 'PTBA', 'ANTM', 'MEDC', 'MYOR'
]

# --- CUSTOM CSS ---
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Poppins', sans-serif !important;
        background-color: #fdf8f6 !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    h1, h2, h3, h4, h5, h6,
    p, span, label, li, div, .stMarkdown p, .stMarkdown div {
        font-family: 'Poppins', sans-serif !important;
        color: #000000 !important;
    }

    .stWidget label, .stSelectbox div, .stSlider div, .stNumberInput input {
        color: #000000 !important;
    }

    [data-testid="stForm"] {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important;
    }

    div[data-baseweb="base-input"], 
    div[data-baseweb="base-input"] > input {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    /* Style Button Standar (Bukan Navigasi) */
    div.stButton > button,
    div.stFormSubmitButton > button {
        background-color: #da6d51 !important;
        color: #ffffff !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        padding: 0.7rem 1.2rem !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }

    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {
        background-color: #759d4e !important;
        color: #ffffff !important;
    }

    /* --- DROPDOWN & POPOVER (KALENDER) PUTIH BERSIH --- */
    div[data-testid="stSelectbox"] {
        width: fit-content !important;
        min-width: 250px !important;
        position: relative;
    }
    
    /* Paksa semua popover, dropdown list, dan kalender jadi putih dan teks hitam */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"] ul,
    div[data-baseweb="calendar"],
    div[data-baseweb="calendar"] div,
    ul[role="listbox"],
    li[role="option"],
    div[data-baseweb="select"],
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    div[data-baseweb="popover"] *,
    div[data-baseweb="select"] *,
    div[data-baseweb="calendar"] * {
        color: #000000 !important;
    }

    li[role="option"]:hover,
    div[data-baseweb="calendar"] [role="button"]:hover {
        background-color: #f0f0f0 !important;
    }

    div[data-baseweb="select"] > div::after {
        content: "▼";
        position: absolute;
        right: 15px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 10px;
        color: #da6d51 !important;
        pointer-events: none;
    }
    
    /* --- TABS --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px !important;
        border-bottom: 2px solid #e2dcd9 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #444444 !important;
        font-weight: 600 !important;
        background-color: transparent !important;
        border-radius: 8px 8px 0px 0px !important;
        padding: 10px 20px !important;
        border: 1px solid transparent !important;
        border-bottom: none !important;
        transition: all 0.25s ease-in-out !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #da6d51 !important;
        border-bottom: 3px solid #da6d51 !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #da6d51 !important;
        background-color: #ffffff !important;
        border: 1px solid #da6d51 !important;
        border-bottom: 3px solid #ffffff !important;
        box-shadow: 0 -4px 10px rgba(0,0,0,0.03) !important;
    }

    /* --- HEADER NAVIGASI CUSTOM CSS --- */
    .top-header-bg {
        position: absolute;
        top: 0;
        left: 0;
        width: 100vw;
        height: 70px;
        background-color: #da6d51; /* Warna Oren */
        z-index: 0;
    }
    
    .block-container {
        padding-top: 1rem !important; /* Dorong konten agar tidak tertutup header */
        z-index: 1;
    }

    /* Mengunci baris header agar tidak wrap dan turun ke bawah */
    div[data-testid="stHorizontalBlock"]:has(.nav-btn) {
        flex-wrap: nowrap !important;
        align-items: center !important;
        height: 50px !important;
    }

    /* Tombol Navigasi */
    div.stButton > button {
        background-color: #da6d51 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    /* Hover */
    div.stButton > button:hover {
        background-color: #759d4e !important;
        color: white !important;
    }

    /* Desain Tombol Navigasi Aktif: Kotak Hijau */
    div.stButton.nav-btn.active-btn > button:first-child {
        background-color: #759d4e !important; /* Warna Hijau */
        color: #ffffff !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- FUNGSI NAVIGASI & HEADER ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'landing'

def navigate_to(page):
    st.session_state.current_page = page

def render_header(current_page_name):

    col_logo, col_space, m1, m2, m3, m4 = st.columns(
        [6, 1.5, 0.8, 1.1, 1, 1.3]
    )

    with col_logo:
        logo_path = BASE_DIR / "Logo" / "Logo_RencanaKita.png"

        st.image(
            str(logo_path),
            width=180
        )

    # Warna tombol aktif
    active_color = "#759d4e"

    if current_page_name == "landing":
        st.markdown(f"""
        <style>
        button[kind="secondary"][data-testid="baseButton-secondary"] {{
            background-color: #da6d51;
        }}
        div[data-testid="stButton"] button[key="nav_home"] {{
            background-color:{active_color} !important;
        }}
        </style>
        """, unsafe_allow_html=True)

    with m1:
        st.button(
            "Home",
            key="nav_home",
            on_click=navigate_to,
            args=("landing",),
            use_container_width=True
        )

    with m2:
        st.button(
            "Education",
            key="nav_edu",
            on_click=navigate_to,
            args=("education",),
            use_container_width=True
        )

    with m3:
        st.button(
            "Forecast",
            key="nav_fore",
            on_click=navigate_to,
            args=("forecast",),
            use_container_width=True
        )

    with m4:
        st.button(
            "Recommend",
            key="nav_rec",
            on_click=navigate_to,
            args=("recommendation",),
            use_container_width=True
        )

    st.write("")
# --- HALAMAN 1: LANDING PAGE ---
def landing_page():
    st.write("<br>", unsafe_allow_html=True)
    col_kiri, col_kanan = st.columns([1.2, 1], gap="large")
    
    with col_kiri:
        st.markdown("<h2> </h2>", unsafe_allow_html=True)
        st.markdown("<h1> </h1>", unsafe_allow_html=True)
        
        st.markdown("<div style='font-size: 3.5rem; font-weight: 800; line-height: 1.2; margin-bottom: 1rem; margin-top: 2rem;'>Mulai Rencanakan<br>Masa Depanmu.</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 1.2rem; margin-bottom: 2rem; line-height: 1.5;'>Analisis portofolio, pelajari instrumen investasi, dan dapatkan prediksi pasar yang dirancang khusus untuk gaya investasimu dalam satu aplikasi.</div>", unsafe_allow_html=True)
        
        st.write(" ")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("Education", on_click=navigate_to, args=('education',), use_container_width=True)
        with c2:
            st.button("Forecast", on_click=navigate_to, args=('forecast',), use_container_width=True)
        with c3:
            st.button("Recommend", on_click=navigate_to, args=('recommendation',), use_container_width=True)
            
    with col_kanan:
            st.write("<br>", unsafe_allow_html=True)
            st.markdown("<h2> </h2>", unsafe_allow_html=True)
            st.markdown("<h2> </h2>", unsafe_allow_html=True)
            
            def get_base64_video():
                video_path = BASE_DIR / "Logo" / "logo.mp4"
                try:
                    with open(video_path, "rb") as file:
                        return base64.b64encode(file.read()).decode()
                except FileNotFoundError:
                    return ""

            video_base64 = get_base64_video()
            if video_base64:
                video_html = f"""
                <div style="display: flex; justify-content: center; align-items: center; height: 100%; pointer-events: none;">
                    <video width="100%" autoplay loop muted playsinline style="border-radius: 24px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">
                        <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
                    </video>
                </div>
                """
                st.markdown(video_html, unsafe_allow_html=True)
            else:
                st.info("[ Video Animasi Logo RencanaKita ]")

# --- HALAMAN 2: EDUCATION ---
def education_page():
    render_header('education')
    
    st.title("Pusat Edukasi Investasi")
    st.markdown("Pelajari istilah fundamental dan berbagai instrumen investasi sebelum memulai.")
    st.write("---")
    
    tab_fondasi, tab_instrumen = st.tabs(["Fondasi Fundamental", "Instrumen Investasi"])
    
    with tab_fondasi:
            st.subheader("3 Langkah Sebelum Mulai Investasi")
            
            # 1. Injeksi CSS Khusus untuk Melengkungkan Sudut Gambar di dalam Box (Alert)
            st.markdown("""
            <style>
            div[data-testid="stAlert"] img {
                border-radius: 16px !important; /* Membuat sudut curve */
                width: 100% !important;         /* Menyesuaikan lebar gambar dengan box */
                margin: 12px 0px !important;    /* Memberi jarak atas bawah */
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); /* Opsional: Efek bayangan tipis */
            }
            </style>
            """, unsafe_allow_html=True)
            
            # 2. Helper Function untuk Konversi Gambar ke Base64
            def get_base64_img(file_name):
                img_path = BASE_DIR / "Logo" / file_name
                try:
                    with open(img_path, "rb") as f:
                        return base64.b64encode(f.read()).decode()
                except FileNotFoundError:
                    return ""

            # Load gambar berdasarkan path di folder Logo
            b64_img1 = get_base64_img("gambar1.png")
            b64_img2 = get_base64_img("gambar2.png")
            b64_img3 = get_base64_img("gambar3.png")

            # 3. Membuat 3 kolom agar sejajar seperti di gambar
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.success(f"""
                **1. Atur Budget (50/30/20)**
                
                ![Langkah 1](data:image/png;base64,{b64_img1})
                
                Pisahkan gajimu: 50% untuk kebutuhan pokok (makan, kos, tagihan), 30% untuk keinginan (ngopi, nonton), dan **20% untuk masa depan (tabungan & investasi)**.
                """)
                
            with col2:
                st.warning(f"""
                **2. Amankan Dana Darurat**
                
                ![Langkah 2](data:image/png;base64,{b64_img2})
                
                Sebelum beli aset apa pun, pastikan kamu punya pegangan uang tunai setara **3 sampai 6 bulan pengeluaranmu**. Ini penting biar kamu gak perlu mencairkan investasi saat ada keadaan darurat.
                """)
                
            with col3:
                st.error(f"""
                **3. Lunasi Utang Konsumtif**
                
                ![Langkah 3](data:image/png;base64,{b64_img3})
                
                Jika masih punya utang dengan bunga tinggi seperti Paylater atau Kartu Kredit, **lunasi itu dulu**. Bunga utang konsumtif biasanya jauh lebih besar daripada keuntungan investasi.
                """)
    with tab_instrumen:
        t_dep, t_rek, t_obl, t_emas, t_sah = st.tabs(["Deposito", "Reksadana", "Obligasi", "Emas", "Saham"])
        
        # --- TAB: DEPOSITO ---
        with t_dep:
            st.markdown("### Level 1: Deposito")
            st.markdown("**Tempat paling aman untuk melindungi uangmu dari inflasi tanpa perlu pusing melihat harga turun.**")
            st.divider()

            st.header("Mari Pahami Konsep Dasarnya")
            st.info("**Apa Itu Deposito?**\n\nDeposito adalah produk simpanan berjangka yang ditawarkan oleh bank. Kamu menyimpan sejumlah uang untuk jangka waktu tertentu (misalnya 1 bulan, 3 bulan, 6 bulan, atau 1 tahun) dan mendapatkan bunga sebagai imbalannya. Setelah jangka waktu berakhir, kamu bisa mencairkan uangmu beserta bunganya.")
            st.info("**Analogi Sederhana:**\n\nMenyimpan uang di Deposito itu ibarat kamu menitipkan uang di brankas bank yang sangat aman, tapi uang itu tidak diam. Uangmu 'bekerja' dengan dipinjamkan ke bank atau negara dalam jangka sangat pendek, dan sebagai gantinya kamu dibayar menggunakan bunga rutin.")

            col1, col2 = st.columns(2)
            with col1:
                st.error("### Musuh Terbesarmu: Inflasi\n\nPernah sadar harga semangkuk mie ayam 5 tahun lalu lebih murah dari sekarang? Itulah inflasi. Kalau kamu cuma menyimpan uang di bawah kasur atau tabungan biasa yang bunganya nyaris 0%, nilai uangmu sebenarnya pelan-pelan 'dimakan' oleh inflasi. Deposito dan Pasar Uang adalah senjata paling dasar untuk melawan inflasi.")
            with col2:
                st.success("### Untuk Siapa Aset Ini?\n\nInstrumen ini sangat wajib dimiliki oleh tipe investor **Averse** (Sangat Menghindari Risiko) dan **Minimalist** (Lebih Suka Keamanan). Selain itu, ini adalah tempat terbaik untuk memarkir **Dana Darurat** karena sifatnya yang stabil dan grafiknya nyaris selalu naik perlahan tanpa *drawdown* (penurunan drastis).")

            st.markdown("### Plus & Minus")
            col_plus, col_minus = st.columns(2)
            with col_plus:
                st.success("**Kelebihan:**\n- **Risiko Sangat Rendah:** Uang di deposito bank umum dijamin oleh LPS (Lembaga Penjamin Simpanan).\n- **Stabil:** Bebas dari serangan panik pasar saham.\n- **Cocok untuk Rencana Jangka Pendek:** Karena mudah dicairkan setelah jatuh tempo, cocok untuk menabung jangka pendek.")
            with col_minus:
                st.warning("**Kekurangan:**\n- **Return Terbatas:** Keuntungannya tidak akan membuatmu cepat kaya, fungsinya lebih ke 'menjaga' kekayaan.\n- **Pajak Cukup Besar:** Bunga deposito dikenakan potongan pajak sebesar 20% oleh pemerintah.\n- **Terkena Penalti Jika Dicairkan Dini:** Jika kamu mencairkan deposito sebelum jatuh tempo, biasanya akan dikenakan penalti berupa potongan bunga atau bahkan pokok.")

            st.divider()
            st.header("Cara Menghitung Bunga Deposito")
            st.write("Sebelum mencoba simulator, mari lihat rumus standar yang digunakan oleh bank:")
            st.latex(r"B = P \times r \times \frac{t}{365}")
            st.markdown("**Keterangan:** **B** = Jumlah bunga (Rp) | **P** = Pokok (*Principal*) | **r** = Suku bunga per tahun | **t** = Tenor penyimpanan (Hari)")

            st.divider()
            st.header("Simulator Pertumbuhan Dana")
            input_col1, input_col2, input_col3 = st.columns(3)
            with input_col1:
                nominal = st.slider("Jumlah Deposito (Rp)", min_value=1_000_000, max_value=500_000_000, value=10_000_000, step=1_000_000)
            with input_col2:
                tenor = st.slider("Tenor / Jangka Waktu (Bulan)", min_value=1, max_value=60, value=12, step=1)
            with input_col3:
                bunga = st.slider("Suku Bunga / Tahun (%)", min_value=1.0, max_value=10.0, value=5.0, step=0.1)

            pajak_rate = 0.20
            bunga_kotor = nominal * (bunga / 100) * (tenor / 12)
            potongan_pajak = bunga_kotor * pajak_rate
            bunga_bersih = bunga_kotor - potongan_pajak
            total_pengembalian = nominal + bunga_bersih

            st.markdown("#### Estimasi Hasil Keuntunganmu")
            res_col1, res_col2, res_col3 = st.columns(3)
            res_col1.metric(label="Bunga Bersih (Milikmu)", value=f"Rp {bunga_bersih:,.0f}")
            res_col2.metric(label="Pajak Negara (20%)", value=f"Rp {potongan_pajak:,.0f}")
            res_col3.metric(label="Total Dana Saat Cair", value=f"Rp {total_pengembalian:,.0f}")

            data_bulan = []
            for bulan in range(1, tenor + 1):
                bunga_bulan_ini = (nominal * (bunga / 100) * (1 / 12)) * (1 - pajak_rate)
                data_bulan.append({"Bulan ke-": bulan, "Total Saldo (Rp)": nominal + (bunga_bulan_ini * bulan)})
            
            # FITUR INTERAKTIF: GRAFIK DEPOSITO
            df_dep = pd.DataFrame(data_bulan)
            fig_dep = px.line(df_dep, x="Bulan ke-", y="Total Saldo (Rp)")
            fig_dep.update_layout(
                template="plotly_white",
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font=dict(color="#000000"),
                xaxis=dict(color="#000000", tickfont=dict(color="#000000")),
                yaxis=dict(color="#000000", tickfont=dict(color="#000000")),
                xaxis_title="Bulan ke-",
                yaxis_title="Total Saldo (Rp)",
                margin=dict(l=20, r=20, t=20, b=20)
            )
            fig_dep.update_traces(line_color="#1f77b4", line_width=2)
            st.plotly_chart(fig_dep, use_container_width=True)

            st.header("💡 Tips Pro: Memaksimalkan Keuntungan Deposito")
            st.warning("**1. Manfaatkan Bank Digital, Tapi Tetap Waspada**\n\nDeposito bank digital menawarkan bunga tinggi hingga 8% p.a. Namun, **LPS hanya menjamin maksimal bunga 6%**. Jika bank bermasalah dan bunga Anda di atas batas penjaminan, risiko ditanggung sendiri!")
            st.success("**2. Trik Legal Menghindari Pajak 20%**\n\nPajak bunga deposito berlaku jika penempatan dana melebihi Rp 7.500.000. Pecah modal menjadi beberapa akun deposito dengan nominal **di bawah Rp 7.500.000** di bank digital secara sah untuk meloloskan diri dari potongan pajak.")
            st.divider()

        # --- TAB: REKSADANA ---
        with t_rek:
            st.markdown("### Level 2: Reksadana (Mutual Funds)")
            st.markdown("**Serahkan pada ahlinya. Beli 'keranjang' berisi berbagai aset hanya dengan satu kali klik.**")
            st.divider()

            st.header("Mari Pahami Konsep Dasarnya")
            st.info("**Apa Itu Reksadana?**\n\nReksadana adalah wadah investasi yang mengumpulkan dana dari banyak investor untuk diinvestasikan ke berbagai instrumen seperti saham, obligasi, atau deposito. Dana dikelola oleh **Manajer Investasi (MI)** profesional. Kamu cukup membeli unit penyertaan, dan biarkan MI bekerja memilih aset terbaik.")
            st.info("**Analogi Sederhana:**\n\nBayangkan kamu ingin makan salad buah yang isinya beraneka ragam (apel, anggur, mangga, kiwi). Membeli tiap buah secara utuh tentu mahal dan repot mengupasnya. Reksadana hadir sebagai porsi wadah 'salad buah' siap konsumsi yang diracik seimbang oleh ahli gizi (**Manajer Investasi**).")
            st.info("**Jenis-Jenis Reksadana:**\n\n- **Reksadana Pasar Uang:** Alokasi ke instrumen pasar uang (deposito, obligasi jangka pendek). Risiko terendah, return stabil.\n- **Reksadana Pendapatan Tetap:** Fokus utama pada obligasi pemerintah/korporasi. Risiko sedang, potensi return lebih tinggi dari pasar uang.\n- **Reksadana Saham:** Mayoritas ditempatkan pada saham emiten. Risiko tinggi, potensi pertumbuhan besar dalam jangka panjang.\n- **Reksadana Campuran:** Kombinasi fleksibel antara saham, obligasi, dan pasar uang.")

            st.success("### Siapa itu Manajer Investasi (MI)?\n\nMereka adalah tim profesional bersertifikat resmi yang memantau dinamika pasar keuangan setiap hari. Dana akumulasi dari seluruh investor dikelola terpadu untuk dibelanjakan ke portofolio instrumen finansial terbaik, sehingga Anda bisa duduk tenang menikmati imbal hasil.")

            st.divider()
            st.markdown("### Untuk Siapa Aset Ini?")
            col_rek1, col_rek2 = st.columns(2)
            with col_rek1:
                st.info("**Pasar Uang & Pendapatan Tetap:**\n- Pasar uang ideal untuk tipe **Averse** & **Minimalist** guna melawan laju inflasi dengan risiko sangat rendah, cocok untuk target jangka pendek (<1 tahun).\n- Pendapatan tetap pas bagi tipe **Cautious** (Moderat) dengan cakrawala target investasi jangka menengah (3-5 tahun).")
            with col_rek2:
                st.success("**Saham & Campuran:**\n- Reksadana Saham sangat klop untuk tipe investor **Open** & **Hungry** (Agresif) yang sibuk dan tidak sempat menganalisis grafik harian.\n- Reksadana Campuran menjembatani investor pemula yang berniat melakukan diversifikasi instrumen secara otomatis.")

            st.markdown("### Plus & Minus")
            col_p_rek, col_m_rek = st.columns(2)
            with col_p_rek:
                st.success("**Kelebihan:**\n- **Praktis:** Seluruh manajemen dilakukan langsung oleh ahlinya.\n- **Diversifikasi Otomatis:** Risiko investasi tersebar luas secara kolektif.\n- **Terjangkau:** Pembelian unit penyertaan dapat dimulai dari modal Rp 10.000.")
            with col_m_rek:
                st.warning("**Kekurangan:**\n- **Expense Ratio:** Pemotongan persentase kecil dari keuntungan bersih untuk biaya operasional kelola jasa MI.\n- **Risiko Pasar:** Nilai aktiva reksadana ikut berfluktuasi searah dengan penurunan pasar modal.")

            st.divider()
            st.header("Cara Kerja Harga Reksadana (NAB)")
            st.write("Keuntungan reksadana bergantung pada pergerakan **NAB/UP (Nilai Aktiva Bersih per Unit Penyertaan)** yang diperbarui berkala:")
            st.latex(r"Unit\ Penyertaan\ (UP) = \frac{Nominal\ Investasi}{Harga\ NAB\ saat\ beli}")
            st.latex(r"Total\ Saldo = Unit\ Penyertaan\ (UP) \times Harga\ NAB\ hari\ ini")
            st.info("**Contoh Nyata:** Beli reksadana senilai Rp 100.000 saat NAB Rp 1.000 mendapat **100 Unit**. Ketika kinerja MI berhasil menaikkan harga NAB ke level Rp 1.200, total saldo Anda bertumbuh menjadi: 100 Unit x Rp 1.200 = **Rp 120.000**.")

            st.divider()
            st.header("Simulator Kekuatan Rutin Menabung (DCA)")
            st.write("Simulasikan jurus penempatan rutin bulanan (*Dollar Cost Averaging*) untuk melipatgandakan aset portofolio:")
            in_r1, in_r2, in_r3, in_r4 = st.columns(4)
            with in_r1: modal_awal = st.slider("Modal Awal (Rp)", 0, 50_000_000, 5_000_000, step=1_000_000, key="ra")
            with in_r2: nabung_rutin = st.slider("Nabung Bulanan (Rp)", 100_000, 10_000_000, 1_000_000, step=100_000, key="rb")
            with in_r3: tenor_tahun = st.slider("Lama Investasi (Tahun)", 1, 30, 10, step=1, key="rc")
            with in_r4: asumsi_return = st.slider("Asumsi Return/Tahun (%)", 1.0, 20.0, 8.0, step=0.5, key="rd")

            bulan_total = tenor_tahun * 12
            asumsi_return_bulanan = (asumsi_return / 100) / 12
            data_perjalanan, saldo_berjalan, modal_terkumpul = [], modal_awal, modal_awal

            for bulan in range(1, bulan_total + 1):
                saldo_berjalan += nabung_rutin
                modal_terkumpul += nabung_rutin
                saldo_berjalan += (saldo_berjalan * asumsi_return_bulanan)
                if bulan % 12 == 0:
                    data_perjalanan.append({"Tahun ke-": int(bulan / 12), "Uang Modalmu (Rp)": modal_terkumpul, "Total Uang + Keuntungan (Rp)": saldo_berjalan})

            res_r1, res_r2, res_r3 = st.columns(3)
            res_r1.metric(label="Uang Modal (Setoran)", value=f"Rp {modal_terkumpul:,.0f}")
            res_r2.metric(label="Keuntungan Hasil MI", value=f"Rp {(saldo_berjalan - modal_terkumpul):,.0f}")
            res_r3.metric(label="Total Saldo Akhir", value=f"Rp {saldo_berjalan:,.0f}")
            
            # FITUR INTERAKTIF: GRAFIK REKSADANA
            df_rek = pd.DataFrame(data_perjalanan)
            fig_rek = px.line(
                df_rek, 
                x="Tahun ke-", 
                y=["Uang Modalmu (Rp)", "Total Uang + Keuntungan (Rp)"],
                color_discrete_sequence=["#1f77b4", "#2ca02c"]
            )
            fig_rek.update_layout(
                template="plotly_white",
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font=dict(color="#000000"),
                xaxis=dict(color="#000000", tickfont=dict(color="#000000")),
                yaxis=dict(color="#000000", tickfont=dict(color="#000000")),
                xaxis_title="Tahun ke-",
                yaxis_title="Nominal (Rp)",
                legend_title_text='',
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_rek, use_container_width=True)

            st.header("💡 Tips Pro: Memilih Reksadana Terbaik")
            st.warning("**1. Perhatikan Expense Ratio (Biaya Manajemen)**\n\nCek data lembar *Fund Fact Sheet*. Cari reksadana dengan *Expense Ratio* rendah (misal di bawah 1.5%) karena efisiensi biaya operasional berbanding lurus dengan optimalnya imbal hasil ke kantong Anda.")
            st.warning("**2. Kejar Kinerja yang Konsisten**\n\nJangan terjebak dengan lonjakan instan semata. Analisis rekam jejak pengembalian instrumen sepanjang jangka 3 bulan, 6 bulan, hingga 1 tahun terakhir untuk memastikan performa stabilitas kelolaan.")
            st.warning("**3. Validasi Total Dana Kelolaan (AUM)**\n\nBesaran nilai *Asset Under Management* (AUM) mencerminkan tingginya skala kredibilitas dan tingkat kepercayaan para pelaku pasar ritel maupun institusional terhadap produk reksadana tersebut.")
            st.success("**4. DCA: Senjata Ampuh Hadapi Pasar Merah**\n\nKetika pasar saham terkoreksi, hindari kepanikan. Strategi DCA otomatis membuat uang bulanan Anda memborong kuantitas **Unit Penyertaan (UP) lebih banyak** di harga murah. Saat pasar kembali pulih, pertumbuhan aset Anda akan melesat eksponensial.")

        # --- TAB: OBLIGASI ---
        with t_obl:
            st.markdown("### Level 4: Obligasi (Surat Utang)")
            st.markdown("**Jadilah 'Bank' bagi Negara atau Perusahaan dan dapatkan bunga rutin yang lebih tinggi dari deposito.**")
            st.divider()

            st.header("Mari Pahami Konsep Dasarnya")
            st.info("**Apa itu Obligasi?**\n\nObligasi adalah penerbitan sertifikat surat utang resmi. Ketika Anda membelinya, Anda memosisikan diri sebagai pihak yang **meminjamkan modal** kepada institusi Negara atau Korporasi. Selaku peminjam, mereka berkewajiban mengembalikan dana pokok utuh saat jatuh tempo di samping menyalurkan transfer kupon bunga periodik.")

            col_ob1, col_ob2 = st.columns(2)
            with col_ob1:
                st.success("### 3 Istilah Utama Obligasi\n\n- **Pari (Nilai Nominal):** Besaran modal pokok dasar pelunasan aset utang.\n- **Kupon:** Komponen bunga berkala yang menjadi hak mutlak investor.\n- **Tenor:** Cakupan jangka masa kontrak utang hingga batas waktu jatuh tempo.")
            with col_ob2:
                st.info("### Klasifikasi Penerbit\n\n- **Pemerintah (SBN):** Instrumen investasi bebas risiko gagal bayar yang dijamin penuh undang-undang negara.\n- **Korporasi:** Surat utang korporasi BUMN/Swasta dengan kompensasi kupon premium.\n- **Sukuk:** Struktur instrumen syariah berbasis prinsip bagi hasil tanpa riba.\n- **Daerah:** Surat utang Pemda guna membiayai fasilitas pembangunan publik lokal.")

            st.divider()
            st.header("Hukum Jungkat-Jungkit Obligasi")
            st.write("Nilai harga obligasi bergerak bertolak belakang terhadap fluktuasi suku bunga acuan pasar:")
            st.latex(r"Price = \sum_{t=1}^{N} \frac{C}{(1+r)^t} + \frac{FV}{(1+r)^N}")
            st.warning("**Rumus Aturan Pasar:**\n- Apabila suku bunga BI acuan **NAIK**, harga obligasi lama Anda di pasar sekunder akan **TURUN**.\n- Apabila suku bunga BI acuan **TURUN**, harga pasar sekunder obligasi Anda otomatis **NAIK** (*Capital Gain*).")

            st.divider()
            st.header("Simulator Obligasi & Risiko Suku Bunga")
            col_in_ob, col_sim_ob = st.columns([1, 2])
            with col_in_ob:
                st.markdown("#### Spesifikasi Obligasi")
                face_val = st.number_input("Nilai Pokok / Pari (Rp)", value=10_000_000, step=1_000_000)
                coupon = st.number_input("Kupon Tahunan (%)", value=6.5, step=0.1) / 100
                tenor_ob = st.number_input("Sisa Tenor (Tahun)", value=10, step=1)
                bond = BondAnalyzer(face_value=face_val, coupon_rate=coupon, years_to_maturity=tenor_ob)

            with col_sim_ob:
                tab_ob1, tab_ob2, tab_ob3 = st.tabs(["Harga Wajar", "Keuntungan Asli (YTM)", "Risiko Durasi"])
                with tab_ob1:
                    ytm_input = st.slider("Simulasi Suku Bunga Pasar (%)", min_value=1.0, max_value=15.0, value=7.0, step=0.1) / 100
                    harga_wajar = bond.calculate_price(ytm_input)
                    status_ob = "Diskon (Lebih Murah)" if harga_wajar < face_val else "Premium (Lebih Mahal)" if harga_wajar > face_val else "Pari ⚖️"
                    st.metric(label="Harga Jual Jaringan Sekunder", value=f"Rp {harga_wajar:,.0f}", delta=status_ob, delta_color="off")
                with tab_ob2:
                    harga_pasar = st.number_input("Harga Beli Pasar Sekunder (Rp):", value=9_500_000, step=100_000)
                    ytm_riil = bond.calculate_ytm(harga_pasar)
                    if ytm_riil > 0:
                        st.metric(label="Yield to Maturity (YTM)", value=f"{ytm_riil * 100:.2f}%")
                        st.success("Membeli di bawah harga Pari (Diskon) mendatangkan imbal bunga riil yang lebih tinggi dibanding nilai kupon tertulis!")
                    else:
                        st.error("Masukkan input nominal harga pasar sekunder dengan valid.")
                with tab_ob3:
                    ytm_risk_input = st.number_input("Suku Bunga Pasar Saat Ini (%)", value=6.5, step=0.1) / 100
                    mod_dur = bond.calculate_modified_duration(ytm_risk_input)
                    st.metric(label="Modified Duration", value=f"{mod_dur:.2f} Tahun")
                    st.warning(f"Estimasi sensitivitas ekonomi: Tiap kenaikan 1% suku bunga acuan berisiko memicu koreksi nilai aset jual obligasi sebesar ~{mod_dur:.2f}%.")

            st.header("💡 Tips Pro: Jurus Anti Rugi")
            st.success("**Strategi Hold to Maturity (Pegang Hingga Lunas)**\n\nJika melihat portofolio obligasi pasar sekunder Anda memerah di dasbor aplikasi, **jangan panik dan jangan gegabah menjualnya**. Selama pihak penerbit (terutama Negara) berdiri tegak, nominal modal pokok awal (Pari) Anda dijamin cair 100% utuh tanpa potongan saat tanggal jatuh tempo tiba.")

        # --- TAB: EMAS ---
        with t_emas:
            st.markdown("### Level 3: Emas (Logam Mulia)")
            st.markdown("**Bukan untuk cepat kaya, tapi untuk menjaga agar kamu tidak jatuh miskin saat terjadi krisis.**")
            st.divider()

            st.header("Mari Pahami Konsep Dasarnya")
            st.info("**Analogi Sederhana:** Emas berperan sebagai komoditas *Safe Haven* utama. Nilai mata uang fiat ibarat kapal kayu di samudra luas; melaju kencang di kala cerah, namun rentan terombang-ambing hancur diterpa badai resesi, perang, atau hiperinflasi ekonomi. Emas hadir layaknya jangkar sekoci baja solid yang menyelamatkan daya beli bersih kekayaan finansial Anda.")

            col_em1, col_em2 = st.columns(2)
            with col_em1:
                st.success("### Pelindung Nilai Riil (Hedging)\n\nUang nominal Rp 10.000 di tahun 1990 bernilai besar, sementara saat ini nilainya menyusut drastis. Berbanding terbalik, daya tukar intrinsik 1 gram emas sejak berabad-abad lampau hingga detik ini terbukti konstan setara nilai beli seekor kambing. Emas tidak memproduksi arus kas deviden, kegunaan mutlaknya adalah membentengi kekayaan dari inflasi.")
            with col_em2:
                st.info("### Untuk Siapa Aset Ini?\n\nEmas sangat direkomendasikan bagi semua profil risiko investor sebagai instrumen penyeimbang stabilitas. Alokasikan kisaran **5% - 10% dari total aset** sebagai proteksi fundamental jangka panjang (>5 tahun) ataupun instrumen persiapan warisan.")

            st.markdown("### Plus & Minus")
            col_p_em, col_m_em = st.columns(2)
            with col_p_em:
                st.success("**Kelebihan:**\n- **Resistensi Krisis:** Kurva nilai emas melonjak tajam kala situasi makro geopolitik dunia bergejolak.\n- **Likuiditas Global:** Berlaku universal dan diakui sah untuk dicairkan di belahan dunia mana pun.\n- **Aset Fisik:** Wujud riil komoditas dapat digenggam dan diamankan mandiri oleh investor.")
            with col_m_em:
                st.warning("**Kekurangan:**\n- **Nihil Passive Income:** Tidak memberikan bagi hasil kupon bunga bulanan.\n- **Beban Penyimpanan:** Adanya risiko pencurian fisik atau konsekuensi biaya sewa kompartemen *Safe Deposit Box*.\n- **Spread Jual Beli:** Selisih antara harga beli awal dengan nilai penjualan kembali (*buyback*).")

            st.divider()
            st.header("Hati-hati dengan SPREAD (Harga Buyback)")
            st.write("Kerap terjadi salah kaprah pemula: Membeli emas ritel seharga Rp 1.300.000 lalu terkejut ketika hendak menjualnya esok hari karena toko hanya menghargai nilai *Buyback* sebesar Rp 1.150.000. Selisih margin harga ini disebut **Spread**.")
            st.latex(r"Spread = Harga\ Beli\ Saat\ Ini - Harga\ Jual\ Kembali\ (Buyback)")
            st.latex(r"Gram\ Didapat = \frac{Nominal\ Uang}{Harga\ Beli\ per\ Gram}")
            st.latex(r"Uang\ Saat\ Dicairkan = Gram\ Dimiliki \times Harga\ Buyback\ Saat\ Itu")
            st.info("**Aturan Main:** Mengingat beban *spread* berkisar 3% - 10%, penempatan dana pada aset emas batangan **wajib diproyeksikan untuk jangka panjang minimal 3-5 tahun** demi melampaui batas potongan harga beli-jual toko.")

            st.divider()
            st.header("Simulator Jebakan Spread Emas")
            st.write("Gunakan simulasi interaktif di bawah untuk melihat kapan garis keuntungan investasi mulai melampaui modal awal pembelanjaan:")
            in_em1, in_em2, in_em3, in_em4 = st.columns(4)
            with in_em1: modal_emas = st.slider("Uang untuk Beli Emas (Rp)", 1_000_000, 100_000_000, 10_000_000, step=1_000_000, key="ea")
            with in_em2: harga_beli_skrg = st.number_input("Harga Beli Saat Ini (Rp/Gram)", value=1_300_000, step=10_000, key="eb")
            with in_em3: spread_persen = st.slider("Asumsi Spread / Potongan Buyback (%)", 1, 15, 5, step=1, key="ec")
            with in_em4: kenaikan_tahunan = st.slider("Asumsi Kenaikan Harga/Tahun (%)", 1.0, 15.0, 6.0, step=0.5, key="ed")

            gram_didapat = modal_emas / harga_beli_skrg
            harga_buyback_skrg = harga_beli_skrg * (1 - (spread_persen / 100))
            nilai_jual_hari_ini = gram_didapat * harga_buyback_skrg
            rugi_hari_pertama = modal_emas - nilai_jual_hari_ini

            res_em1, res_em2, res_em3 = st.columns(3)
            res_em1.metric(label="Total Berat Logam didapat", value=f"{gram_didapat:.2f} Gram")
            res_em2.metric(label="Likuidasi Instan Hari Pertama", value=f"Rp {nilai_jual_hari_ini:,.0f}", delta=f"- Rp {rugi_hari_pertama:,.0f}", delta_color="inverse")
            res_em3.info(f"Hal ini terjadi akibat ketetapan kuotasi harga beli balik (*Buyback*) penyedia emas hari ini bernilai Rp {harga_buyback_skrg:,.0f}/gram.")

            data_emas = []
            for tahun in range(0, 11):
                harga_beli_tahun_ini = harga_beli_skrg * ((1 + (kenaikan_tahunan / 100)) ** tahun)
                nilai_pencairan = gram_didapat * (harga_beli_tahun_ini * (1 - (spread_persen / 100)))
                data_emas.append({"Tahun ke-": tahun, "Modal Awalku (Rp)": modal_emas, "Nilai Pencairan Emas (Rp)": nilai_pencairan})
            
            # FITUR INTERAKTIF: GRAFIK EMAS
            df_emas = pd.DataFrame(data_emas)
            fig_emas = px.line(
                df_emas, 
                x="Tahun ke-", 
                y=["Modal Awalku (Rp)", "Nilai Pencairan Emas (Rp)"],
                color_discrete_sequence=["#1f77b4", "#ffb300"]
            )
            fig_emas.update_layout(
                template="plotly_white",
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font=dict(color="#000000"),
                xaxis=dict(color="#000000", tickfont=dict(color="#000000")),
                yaxis=dict(color="#000000", tickfont=dict(color="#000000")),
                xaxis_title="Tahun ke-",
                yaxis_title="Nominal (Rp)",
                legend_title_text='',
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_emas, use_container_width=True)

            st.header("💡 Tips Pro: Memaksimalkan Investasi Emas")
            st.warning("**1. JANGAN Menjadikan Emas Perhiasan Sebagai Sarana Investasi Utama!**\n\nKetika memborong kalung, cincin, atau gelang, Anda dibebankan komponen 'Ongkos Pembuatan' yang tinggi. Sayangnya, saat dijual kembali, pihak toko murni mengalkulasi timbangan berat kadar emas semata (ongkos bikin hangus). Selalu prioritaskan **Emas Batangan / Logam Mulia Murni (Antam/UBS)**.")
            st.success("**2. Optimalisasi Alokasi Emas Digital vs Fisik**\n\nBagi langkah awal bermodal minim, manfaatkan platform **Emas Digital** berizin resmi OJK yang memfasilitasi transaksi mulai dari Rp 10.000. Tabungan digital meminimalisasi risiko kehilangan fisik dan menawarkan spread yang bersaing. Cetak fisik batangan baru diajukan pasca saldo terkumpul di atas ambang 5-10 gram.")

        # --- TAB: SAHAM (UPDATED INTERAKTIF) ---
        with t_sah:
            st.markdown("### Level 5: Saham (Equities)")
            st.markdown("**Beli bisnisnya, bukan sekadar menebak grafik. Jadilah pemilik dari perusahaan-perusahaan raksasa.**")
            st.divider()

            st.header("Pahami Mindset yang Benar")
            st.info("**Apa itu Saham?**\n\nSaham merepresentasikan bukti kepemilikan valid atas porsi modal di suatu korporasi/perusahaan. Dengan membeli lembar saham emiten, Anda menempatkan diri sebagai pemilik bagian dari lini bisnis operasional tersebut.")
            st.info("**Analogi Pendirian Usaha:**\n\nIbarat rekan sejawat mendirikan kedai kopi bermodal patungan Rp 100 juta yang dipecah kepemilikannya ke dalam 100 lembar akta (Rp 1 juta/lembar). Apabila Anda membeli hak kepemilikan sebanyak 10 lembar, Anda sah menguasai 10% bisnis kedai kopi tersebut, berhak atas bagi hasil profit bulanan, sekaligus ikut memikul risiko jika performa kedai sepi pembeli.")

            st.header("Faktor Penggerak Fluktuasi Harga Pasar")
            st.write("Dinamika pergerakan angka indeks harga saham dipengaruhi sentimen multisektoral secara berkesinambungan:")
            col_sh1, col_sh2, col_sh3 = st.columns(3)
            with col_sh1:
                st.success("**Kinerja Finansial Internal**\n\nIndikator penggerak utama pasar:\n- **Pertumbuhan Laba Bersih:** Memicu aksi beli kolektif investor, harga merangkak naik.\n- **Penyusutan Pendapatan:** Mendorong aksi lego saham, memicu harga terkoreksi.")
            with col_sh2:
                st.warning("**Katalis Makro Ekonomi**\n\nSentimen eksternal di luar korporasi:\n- **Ekonomi Ekspansif:** Daya beli masyarakat solid, bursa menghijau.\n- **Ancaman Resesi global:** Suku bunga melonjak, menekan kinerja pasar modal.")
            with col_sh3:
                st.info("**Psikologi & Sentimen Pasar**\n\nSiklus fluktuasi emosi ketakutan (*fear*) & keserakahan (*greed*):\n- **Berita Positif:** Perolehan tender mega proyek memicu akselerasi harga.\n- **Kabar Negatif:** Rumor fraud struktural memicu aksi jual panik (*panic selling*).")

            col_cu1, col_cu2 = st.columns(2)
            with col_cu1:
                st.success("### Sumber Keuntungan Investasi Saham\n\n1. **Capital Gain:** Keuntungan yang diraih dari selisih margin harga jual di atas harga beli semula.\n2. **Dividen:** Pembagian porsi keuntungan bersih hasil kelola usaha emiten yang ditransfer tunai kepada pemilik saham.")
            with col_cu2:
                st.warning("### Untuk Siapa Arena Investasi Ini?\n\nSaham merupakan instrumen agresif bagi profil tipe investor **Open** dan **Hungry**. Mengingat volatilitasnya yang sangat dinamis, alokasikan penempatan aset murni menggunakan **uang dingin** (dana mengendap yang dijamin tidak terpakai untuk keperluan primer minimal 5 tahun ke depan).")

            st.divider()
            st.header("Analisa Pergerakan Harga Saham")
            st.write("Pilih emiten dan atur rentang waktu untuk melihat visualisasi pergerakan harga. Arahkan kursor (hover) ke batang *candlestick* untuk melihat harga Open, High, Low, Close, dan Volume pada tanggal tersebut.")

            pilihan_saham = st.selectbox("Pilih Emiten yang Ingin Kamu Analisa:", daftar_emiten)
            df_pilihan = load_stock_data(pilihan_saham)

            if not df_pilihan.empty:
                min_date = df_pilihan['Date'].min().date()
                max_date = df_pilihan['Date'].max().date()
                
                date_range = st.date_input(
                    "Pilih Rentang Waktu Analisa:",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
                
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    mask = (df_pilihan['Date'].dt.date >= start_date) & (df_pilihan['Date'].dt.date <= end_date)
                    df_filtered = df_pilihan.loc[mask].copy()
                else:
                    df_filtered = df_pilihan.copy()
                    
                # Menggunakan Volume jika ada
                if 'Volume' in df_filtered.columns:
                    vol_data = df_filtered['Volume']
                else:
                    vol_data = pd.Series([0] * len(df_filtered), index=df_filtered.index)

                # Merakit string hovertext manual menggunakan Pandas untuk menghindari error hovertemplate
                hover_text = (
                    "<b>Tanggal: </b>" + df_filtered['Date'].dt.strftime('%Y-%m-%d') + "<br><br>" +
                    "Open: Rp " + df_filtered['Open'].map('{:,.0f}'.format) + "<br>" +
                    "High: Rp " + df_filtered['High'].map('{:,.0f}'.format) + "<br>" +
                    "Low: Rp " + df_filtered['Low'].map('{:,.0f}'.format) + "<br>" +
                    "Close: Rp " + df_filtered['Close'].map('{:,.0f}'.format) + "<br>" +
                    "Volume: " + vol_data.map('{:,.0f}'.format)
                )

                # Grafik Candlestick Interaktif (Menggunakan text dan hoverinfo="text")
                fig = go.Figure(data=[go.Candlestick(
                    x=df_filtered['Date'],
                    open=df_filtered['Open'],
                    high=df_filtered['High'],
                    low=df_filtered['Low'],
                    close=df_filtered['Close'],
                    text=hover_text,
                    hoverinfo="text",
                    increasing_line_color='#00C853', # Hijau
                    decreasing_line_color='#D50000', # Merah
                    name='Harga Saham'
                )])
                
                # Memaksa warna background putih 
                fig.update_layout(
                    title=f"Pergerakan Harga Saham {pilihan_saham}",
                    template="plotly_white", 
                    xaxis_title="Tanggal",
                    yaxis_title="Harga (Rp)",
                    margin=dict(l=20, r=20, t=50, b=20),
                    plot_bgcolor="#ffffff",
                    paper_bgcolor="#ffffff",
                    font=dict(color="#000000"),
                    xaxis=dict(
                        color="#000000", 
                        tickfont=dict(color="#000000"),
                        rangeslider=dict(visible=False) # Menyembunyikan rangeslider bawah agar lebih rapi
                    ),
                    yaxis=dict(color="#000000", tickfont=dict(color="#000000")),
                )
                
                st.plotly_chart(fig, use_container_width=True)
                

                st.markdown("### Info Emiten")
                with st.container(border=True):
                    if pilihan_saham == 'BBCA':
                        st.info(f"**Info {pilihan_saham}:** BBCA (Bank Central Asia) merupakan bank swasta terbesar di Indonesia. Fundamental yang sangat kokoh membuatnya sering dijuluki 'Rajanya Saham Blue Chip'.")
                    elif pilihan_saham == 'BBRI':
                        st.info(f"**Info {pilihan_saham}:** BBRI fokus pada penyaluran kredit UMKM dan memiliki jaringan terluas hingga ke pelosok, menjadikannya salah satu mesin pencetak laba terbesar di bursa.")
                    elif pilihan_saham == 'BMRI':
                        st.info(f"**Info {pilihan_saham}:** BMRI (Bank Mandiri) adalah bank BUMN dengan total aset terbesar di Indonesia, memiliki keunggulan kuat di segmen kredit korporasi dan komersial.")
                    elif pilihan_saham == 'BBNI':
                        st.info(f"**Info {pilihan_saham}:** BBNI (Bank Negara Indonesia) merupakan bank BUMN yang unggul dalam jaringan internasional dan fokus pada transformasi perbankan digital serta korporasi.")
                    elif pilihan_saham == 'TLKM':
                        st.info(f"**Info {pilihan_saham}:** TLKM (Telkom Indonesia) merupakan pemimpin pangsa pasar telekomunikasi di Indonesia. Sektor defensif yang cocok untuk menjaga stabilitas portofolio.")
                    elif pilihan_saham == 'ASII':
                        st.info(f"**Info {pilihan_saham}:** ASII (Astra International) adalah konglomerasi raksasa di sektor otomotif, alat berat, hingga finansial. Kinerjanya sering dijadikan barometer ekonomi nasional.")
                    elif pilihan_saham == 'ICBP':
                        st.info(f"**Info {pilihan_saham}:** ICBP (Indofood CBP) adalah produsen Indomie dan raksasa *consumer goods*. Emiten defensif yang kebal krisis karena memproduksi barang kebutuhan sehari-hari.")
                    elif pilihan_saham == 'CUAN':
                        st.info(f"**Info {pilihan_saham}:** CUAN (Petrindo Jaya Kreasi) bergerak di sektor pertambangan mineral dan batu bara. Saham ini dikenal memiliki pergerakan harga yang cukup volatil dan agresif.")
                    elif pilihan_saham == 'INCO':
                        st.info(f"**Info {pilihan_saham}:** INCO (Vale Indonesia) adalah produsen nikel terkemuka. Prospek jangka panjangnya diuntungkan oleh tren transisi energi dan industri baterai kendaraan listrik (EV).")
                    elif pilihan_saham == 'ISAT':
                        st.info(f"**Info {pilihan_saham}:** ISAT (Indosat Ooredoo Hutchison) merupakan raksasa telekomunikasi kedua terbesar di Indonesia dengan pertumbuhan bisnis yang sangat agresif pasca merger.")
                    elif pilihan_saham == 'ADRO':
                        st.info(f"**Info {pilihan_saham}:** ADRO (Adaro Energy) adalah raksasa batu bara berskala global. Pergerakan harganya sangat bergantung pada fluktuasi siklus harga komoditas energi dunia.")
                    elif pilihan_saham == 'PTBA':
                        st.info(f"**Info {pilihan_saham}:** PTBA (Bukit Asam) adalah BUMN tambang batu bara yang sangat digemari investor karena rekam jejaknya yang rutin membagikan dividen dalam rasio besar.")
                    elif pilihan_saham == 'ANTM':
                        st.info(f"**Info {pilihan_saham}:** ANTM (Aneka Tambang) merupakan BUMN pengelola tambang emas, nikel, dan bauksit. Sentimen harganya kerap berkorelasi positif dengan pergerakan harga emas global.")
                    elif pilihan_saham == 'MEDC':
                        st.info(f"**Info {pilihan_saham}:** MEDC (Medco Energi) adalah perusahaan migas dan energi terkemuka. Volatilitas sahamnya sangat dipengaruhi oleh sentimen pergerakan harga minyak mentah dunia.")
                    elif pilihan_saham == 'MYOR':
                        st.info(f"**Info {pilihan_saham}:** MYOR (Mayora Indah) adalah produsen makanan ringan dan minuman kemasan (seperti Kopiko) yang mendominasi pasar ekspor global. Sektornya tergolong defensif.")
                    else:
                        st.info(f"**Info {pilihan_saham}:** Belum ada informasi spesifik untuk emiten ini di dalam database.")

            else:
                st.warning(f"Grafik tidak dapat ditampilkan. Pastikan file database untuk {pilihan_saham} tersedia di dalam folder 'Data' dengan kolom Date, Open, High, Low, Close, dan Volume.")

            st.divider()
            st.header("Membaca Fundamental Perusahaan")
            st.write("Sebelum mengevaluasi teknikal pergerakan harga grafik, pastikan fondasi kesehatan manajemen bisnis internal emiten teruji prima:")
            col_fd1, col_fd2 = st.columns(2)
            with col_fd1:
                st.success("**1. ROE (Return on Equity)**\n\nMetrik yang merepresentasikan kepiawaian manajemen dalam mencetak akumulasi laba bersih bersumber dari modal yang Anda tempatkan. Rasio ROE konsisten di atas batas 15% mengindikasikan efisiensi mesin bisnis berjalan sangat tangguh.")
            with col_fd2:
                st.warning("**2. PBV (Price to Book Value)**\n\nRasio komparasi menilai apakah harga pasar saham saat ini tergolong murah atau kemahalan dibanding aset bersihnya. Angka PBV = 1 menandakan valuasi harga wajar, sedangkan emiten berfundamental mapan dengan skor PBV < 1 mengisyaratkan peluang diskon harga masif.")

            st.header("💡 Tips Pro: Bertahan Hidup di Pasar Saham")
            st.error("**Disiplin Ketat: Hindari Jeratan Spekulasi Saham Gorengan!**\n\nInvestor pemula sangat dilarang berspekulasi pada saham berkapitalisasi pasar mikro yang tidak jelas model bisnisnya, meski menjanjikan lonjakan ratusan persen dalam hitungan jam. Risiko suspensi dan kejatuhan harga permanen mengintai modal Anda. Awali langkah perjalanan investasi Anda melalui kepemilikan emiten papan utama *Blue-Chip* penguasa pasar.")
# ==========================================
# FUNGSI FEATURE ENGINEERING UNTUK FORECAST
# ==========================================
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def feature_engineering(df, is_emas=False):
    df = df.copy()

    # 1. Time Features
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        df['Month'] = df['Date'].dt.month
        df['Quarter'] = df['Date'].dt.quarter
        df['Day'] = df['Date'].dt.day
        df['Year'] = df['Date'].dt.year

    # 2. Return
    df['Return'] = df['Close'].pct_change()
    df["Weekly_Return"] = df['Close'].pct_change(periods=5)

    # 3. Lag Features (Gabungan referensi 1 & 2)
    lag_list = [1, 2, 3, 5, 7, 10, 14, 20, 30, 60, 90, 180]
    for lag in lag_list:
        df[f'Lag_Close_{lag}'] = df['Close'].shift(lag)
        if lag in [1, 2, 3, 5, 10, 20]:
            df[f'Lag_Return_{lag}'] = df['Return'].shift(lag)

    # 4. Volatility
    df['Rolling_Vol_7'] = df['Return'].rolling(7).std()
    df['Rolling_Vol_14'] = df['Return'].rolling(14).std()
    df['Rolling_Vol_20'] = df['Return'].rolling(20).std()
    df['Rolling_Vol_30'] = df['Return'].rolling(30).std()

    # 5. Moving Average (Gabungan)
    ma_list = [5, 7, 10, 14, 20, 30]
    for ma in ma_list:
        df[f'SMA_{ma}'] = df['Close'].rolling(ma).mean()

    # 6. EMA & MACD
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']

    # 7. RSI
    df['RSI'] = calculate_rsi(df['Close'], 14)

    # 8. Volume Feature
    if (not is_emas) and ('Volume' in df.columns):
        df['SMA_Vol_5'] = df['Volume'].rolling(5).mean()
        df['SMA_Vol_20'] = df['Volume'].rolling(20).mean()
        for lag in [1, 2, 3, 5, 10, 20]:
            df[f'Lag_Vol_{lag}'] = df['Volume'].shift(lag)

    # 9. Target (Harga besok)
    df["Target"] = df["Close"].shift(-1)

    # Cleanup
    df.dropna(inplace=True)
    return df

# --- HALAMAN 3: FORECAST (UPDATED) ---
def forecast_page():
    render_header('forecast')
    
    st.title("Visualisasi Forecast")
    st.markdown("Prediksi pergerakan instrumen selama 90 hari ke depan berdasarkan *Historical Data*.")
    
    assets = ["Emas"] + daftar_emiten
    selected_asset = st.selectbox("Pilih Instrumen:", assets)
    st.write("---")
    
    # Supaya mapping ke load_stock_data pas dengan file "EMAS_clean.csv"
    ticker_name = "EMAS" if selected_asset == "Emas" else selected_asset
    
    # Load Data Aktual
    df_raw = load_stock_data(ticker_name)
    
    if df_raw.empty:
        st.warning(f"Data untuk {selected_asset} tidak ditemukan. Pastikan file clean.csv tersedia.")
        return
        
    # Proses Feature Engineering
    df_eng = feature_engineering(df_raw, is_emas=(ticker_name == "EMAS"))
    
    # Menggunakan SEMUA data historis yang tersedia (tidak dibatasi 120 hari lagi)
    hist_df = df_eng.copy()
    
    if hist_df.empty:
        st.warning("Data historis tidak mencukupi setelah di-filter.")
        return

    # --- SIMULASI FORECAST 90 HARI (Ganti ini nanti dengan model ML-mu) ---
    last_date = hist_df['Date'].iloc[-1]
    last_price = hist_df['Close'].iloc[-1]
    
    # Buat list tanggal 90 hari bursa ke depan
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=90, freq='B')
    
    # Simulasi prediksi harga (Random Walk / Dummy Model menggunakan keseluruhan data)
    # NANTI GANTI BARIS INI: y_fore = forecast_90_results[ticker_name]
    np.random.seed(42)
    mean_ret = hist_df['Return'].mean()
    std_ret = hist_df['Return'].std()
    simulated_returns = np.random.normal(loc=mean_ret, scale=std_ret, size=90)
    
    future_prices = [last_price * (1 + simulated_returns[0])]
    for r in simulated_returns[1:]:
        future_prices.append(future_prices[-1] * (1 + r))
    # -----------------------------------------------------------------------

    # Hubungkan titik terakhir historis dengan titik awal forecast agar garis menyambung
    x_fore = [last_date] + future_dates.tolist()
    y_fore = [last_price] + future_prices

    # Kalkulasi Support & Resistance dinamis untuk Insight
    min_price = min(hist_df['Close'].min(), min(y_fore))
    max_price = max(hist_df['Close'].max(), max(y_fore))

    col_img, col_text = st.columns([2, 1], gap="large")
    
    with col_img:
        st.markdown(f"**Grafik Interaktif Prediksi 90 Hari - {selected_asset}**")
        
        # Inisialisasi Kanvas Plotly
        fig = go.Figure()

        # 1. Garis Historis (Biru)
        fig.add_trace(go.Scatter(
            x=hist_df['Date'],
            y=hist_df['Close'],
            mode='lines',
            name='Historical (Seluruh Data)',
            line=dict(color='#1f77b4', width=2.5)
        ))

        # 2. Garis Forecast (Oren Putus-putus)
        fig.add_trace(go.Scatter(
            x=x_fore,
            y=y_fore,
            mode='lines',
            name='Forecast (90 Days)',
            line=dict(color='#ff7f0e', width=2.5, dash='dash')
        ))

        # Layout Interaktif & Selector Waktu
        fig.update_layout(
            template="plotly_white",
            hovermode="x unified",
            font=dict(color="#000000"), # Memaksa warna font dasar chart jadi hitam
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1B", step="month", stepmode="backward"),
                        dict(count=3, label="3B", step="month", stepmode="backward"),
                        dict(count=6, label="6B", step="month", stepmode="backward"),
                        dict(count=1, label="1T", step="year", stepmode="backward"),
                        dict(step="all", label="Semua")
                    ]),
                    bgcolor="#ffffff", 
                    activecolor="#da6d51",
                    font=dict(color="#000000") # Warna teks tombol selector
                ),
                type="date",
                title="Tanggal",
                color="#000000",
                tickfont=dict(color="#000000") # Warna teks axis X
            ),
            yaxis=dict(
                title="Harga (IDR)",
                color="#000000",
                tickfont=dict(color="#000000") # Warna teks axis Y
            ),
            margin=dict(l=20, r=20, t=30, b=20),
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            legend=dict(
                orientation="h", 
                yanchor="bottom", 
                y=1.02, 
                xanchor="right", 
                x=1,
                font=dict(color="#000000") # Warna teks legend
            )
        )

        st.plotly_chart(fig, use_container_width=True)
        
    with col_text:
        
        st.markdown("<h2> </h2>", unsafe_allow_html=True)
        st.markdown("**Insight & Deskripsi**")
        with st.container(border=True):
            st.markdown(f"**Brief Market Analysis: {selected_asset}**")
            st.write(f"- Berdasarkan *Machine Learning Forecasting*, prediksi menunjukkan potensi arah tren {selected_asset} untuk 90 hari ke depan.")
            st.write(f"- **Estimasi Level Support:** Rp {min_price:,.0f}")
            st.write(f"- **Estimasi Level Resistance:** Rp {max_price:,.0f}")

# ==========================================
# CLASS ENGINE ROBO ADVISOR
# ==========================================
class RoboAdvisorEngine:
    def __init__(self, model_path=BASE_DIR / 'Model' / 'model_rekomendasi.joblib'): # UPDATED
        """
        Inisialisasi engine: Meload model ML dan menyiapkan data pasar dari CSV.
        """
        # MENGGUNAKAN BASE_DIR UNTUK MODEL PATH
        if model_path is None:
            model_path = BASE_DIR / 'Model' / 'model_rekomendasi.joblib'
            
        # 1. LOAD MODEL MACHINE LEARNING
        try:
            model_pack = joblib.load(model_path)
            self.preprocessor = model_pack['preprocessor']
            self.pca = model_pack['pca']
            self.kmeans = model_pack['kmeans_model']
            self.features = model_pack['feature_names']
        except Exception as e:
            st.error(f"Gagal meload model: {e}")
            
        # 2. SETUP DATA PASAR & COVARIANCE MATRIX (LEDOIT-WOLF)
        self.aset_names = ['Saham', 'Emas', 'Obligasi', 'RDPU', 'Deposito']
        self.expected_returns_annual = self._generate_market_data()
        
        # Mapping Aturan Batas (Hard Constraints) per Cluster
        self.cluster_rules = {
            0: { # AGRESIF
                'nama': 'Agresif (Young & Hungry)',
                'bounds': ((0.10, 0.80), (0.0, 0.20), (0.0, 1.0), (0.0, 1.0), (0.0, 0.10))
            },
            1: { # KONSERVATIF 
                'nama': 'Konservatif (The Pragmatist)',
                'bounds': ((0.0, 0.15), (0.0, 0.20), (0.0, 1.0), (0.0, 1.0), (0.0, 0.10))
            },
            2: { # MODERAT 
                'nama': 'Moderat (Long-Term Planner)',
                'bounds': ((0.0, 0.40), (0.0, 0.20), (0.0, 1.0), (0.0, 1.0), (0.0, 0.15))
            }
        }

    def _generate_market_data(self):
        """
        Membaca data historis dari pelbagai CSV, menghitung return, 
        dan membuat matriks kovarians Ledoit-Wolf.
        """
        try:
            # ==========================================
            # 1. PROSES DATA SAHAM 
            # ==========================================
            file_mapping = {
                'ADRO': 'ADRO_clean.csv', 'ANTM': 'ANTM_clean.csv', 'ASII': 'ASII_clean.csv',
                'BBCA': 'bbca_clean.csv', 'BBNI': 'bbni_clean.csv', 'BBRI': 'bbri_clean.csv',
                'BMRI': 'bmri_clean.csv', 'CUAN': 'CUAN_clean.csv', 'ICBP': 'icbp_clean.csv',
                'INCO': 'INCO_clean.csv', 'ISAT': 'ISAT_clean.csv', 'MEDC': 'MEDC_clean.csv',
                'MYOR': 'myor_clean.csv', 'PTBA': 'PTBA_clean.csv', 'TLKM': 'tlkm_clean.csv' 
            }
            # MENGGUNAKAN BASE_DIR UNTUK MENGUNCI LOKASI FOLDER DATA
            saham_files = [BASE_DIR / "Data" / fname for fname in file_mapping.values()]
            
            list_return_saham = []
            
            for file in saham_files:
                df = pd.read_csv(file)
                # Paksa semua header menjadi huruf besar (CAPSLOCK) supaya seragam
                df.columns = df.columns.str.upper() 
                # Pastikan kolom DATE jadi datetime dan set sebagai index
                df['DATE'] = pd.to_datetime(df['DATE'])
                df = df.set_index('DATE')
                # Kira peratusan perubahan harian (return) dari harga CLOSE
                ret = df['CLOSE'].pct_change()
                list_return_saham.append(ret)
                
            # Gabungkan semua saham bersebelahan antara satu sama lain
            df_saham_all = pd.concat(list_return_saham, axis=1)
            # Cari purata (mean) merentas lajur untuk dapatkan 1 nilai wakil saham setiap hari
            return_saham = df_saham_all.mean(axis=1)
            return_saham.name = 'Saham'

            # ==========================================
            # 2. PROSES DATA EMAS 
            # ==========================================
            df_emas = pd.read_csv(BASE_DIR / "Data" / 'EMAS_clean.csv') # MENGGUNAKAN BASE_DIR
            df_emas.columns = df_emas.columns.str.upper()
            df_emas['DATE'] = pd.to_datetime(df_emas['DATE'])
            df_emas = df_emas.set_index('DATE')
            
            return_emas = df_emas['CLOSE'].pct_change()
            return_emas.name = 'Emas'

            # ==========================================
            # 3. GABUNGKAN SAHAM & EMAS (Inner Join by Date)
            # ==========================================
            df_returns = pd.concat([return_saham, return_emas], axis=1).dropna()

            # ==========================================
            # 4. TAMBAHKAN INSTRUMEN FIXED INCOME (Pendapatan Tetap)
            # ==========================================
            n_days = len(df_returns)
            np.random.seed(42)
            
            # Asumsi pulangan tahunan: Obligasi 7%, RDPU 5%, Deposito 4%
            df_returns['Obligasi'] = np.random.normal((0.07/252), 0.001, n_days) 
            df_returns['RDPU'] = 0.05 / 252      
            df_returns['Deposito'] = 0.04 / 252  
            
            # Susun ikut turutan
            df_returns = df_returns[['Saham', 'Emas', 'Obligasi', 'RDPU', 'Deposito']]

            # ==========================================
            # 5. KALKULASI LEDOIT-WOLF
            # ==========================================
            lw = LedoitWolf()
            lw.fit(df_returns)
            self.cov_matrix_annual = lw.covariance_ * 252
            
            expected_returns = df_returns.mean().values * 252
            return expected_returns
            
        except Exception as e:
            st.error(f"Error saat memproses data pasar: {e}\nPastikan folder Data/ lengkap.")
            return np.array([0.12, 0.08, 0.07, 0.05, 0.04])

    def _markowitz_objective(self, weights, risk_aversion, gamma=0.05):
        """
        Fungsi Utilitas Markowitz dengan L2 Regularization (Diversification Penalty).
        """
        port_return = np.sum(self.expected_returns_annual * weights)
        port_variance = np.dot(weights.T, np.dot(self.cov_matrix_annual, weights))
        l2_penalty = np.sum(weights**2)
        utility = port_return - (0.5 * risk_aversion * port_variance) - (gamma * l2_penalty)
        return -utility 

    def predict_portfolio(self, user_data_dict):
        """Fungsi Prediksi dan Optimasi (Dipanggil dari UI Streamlit)"""
        df_input = pd.DataFrame([user_data_dict])
        df_input = df_input[self.features]
        
        # 1. ML Predict Cluster
        X_scaled = self.preprocessor.transform(df_input)
        X_pca = self.pca.transform(X_scaled)
        cluster_id = self.kmeans.predict(X_pca)[0]
        
        # 2. Setup Batasan MVO
        cluster_info = self.cluster_rules[cluster_id]
        bounds = cluster_info['bounds']
        
        # Skala user_risk_tol diubah menjadi 1-5 (dari tadinya 1-10)
        # Menyesuaikan rasio aversi risiko: 15 / (risk_tol * 2) agar setara
        user_risk_tol = max(user_data_dict.get('risk_tolerance', 1), 1)
        risk_aversion = 15 / (user_risk_tol * 2)
        
        # 3. Optimasi Scipy
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})
        init_guess = np.array([0.2, 0.2, 0.2, 0.2, 0.2]) 
        
        gamma_value = 0.05
        optimized = sco.minimize(
            self._markowitz_objective, 
            init_guess, 
            args=(risk_aversion, gamma_value), 
            method='SLSQP', 
            bounds=bounds, 
            constraints=constraints
        )
        weights = optimized.x
        
        exp_return = np.sum(self.expected_returns_annual * weights)
        exp_risk = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix_annual, weights)))
        
        return {
            'Cluster_ID': cluster_id,
            'Profil': cluster_info['nama'],
            'Alokasi': {self.aset_names[i]: round(weights[i] * 100, 2) for i in range(5)},
            'Proyeksi_Return_Tahunan': round(exp_return * 100, 2),
            'Proyeksi_Risiko': round(exp_risk * 100, 2)
        }

# Caching class engine agar tidak membaca seluruh file CSV setiap kali slider digeser
@st.cache_resource
def get_robo_engine():
    return RoboAdvisorEngine()

# --- HALAMAN 4: RECOMMENDATION ---
def recommendation_page():
    render_header('recommendation')
    
    st.title("Rekomendasi Portofolio")
    st.markdown("Masukkan profil finansial Anda untuk mendapatkan rekomendasi alokasi investasi yang dipersonalisasi.")
    
    # Inisiasi engine ML
    engine = get_robo_engine()
    
    with st.form("recommendation_form", border=True):
        st.subheader("Profil Finansial Anda")
        col1, col2 = st.columns(2, gap="large")
        with col1:
            age = st.number_input("Umur (Tahun)", min_value=17, max_value=100, step=1, value=25)
            monthly_income = st.number_input("Pendapatan Bulanan (Rp)", min_value=1_000_000, value=10_000_000, step=500_000)
            investment_horizon = st.slider("Horizon Investasi (Tahun)", min_value=1, max_value=20, value=5)
        with col2:
            # Toleransi Risiko diubah menjadi 1-5 sesuai permintaan
            risk_tolerance = st.slider("Toleransi Risiko (1=Konservatif, 5=Agresif)", 1, 5, 3)
            investment_goal = st.selectbox("Tujuan Investasi", ["Retirement", "Education", "Emergency Fund", "Wealth Growth", "Lainnya"])
            
        st.write("")
        submit = st.form_submit_button("Generate Rekomendasi Portofolio")
        
    if submit:
        # Menyatukan data input dari User ke dalam Dictionary
        user_data = {
            'risk_tolerance': risk_tolerance, 
            'monthly_income': monthly_income,
            'investment_horizon': investment_horizon, 
            'age': age, 
            'investment_goal': investment_goal
        }
        
        # Mengeksekusi Prediksi ML
        res = engine.predict_portfolio(user_data)
        
        st.success("Data berhasil diproses.")
        st.markdown("### Hasil Rekomendasi Alokasi")
        
        with st.container(border=True):
            st.markdown(f"#### Profil: **{res['Profil']}**")
            
            # Sortir alokasi dari yang terbesar ke terkecil
            sorted_alloc = sorted(res['Alokasi'].items(), key=lambda x: x[1], reverse=True)
            
            # Merender progress bar hasil rekomendasi
            for aset, pct in sorted_alloc:
                if pct > 0:
                    val = max(0, min(100, int(round(pct)))) # Konversi persentase ke int format
                    st.progress(val, text=f"{aset}: {pct}%")
            
            st.divider()
            
            c1, c2 = st.columns(2)
            c1.metric(label="Proyeksi Return (Tahunan)", value=f"{res['Proyeksi_Return_Tahunan']}%")
            c2.metric(label="Proyeksi Risiko (Volatilitas)", value=f"{res['Proyeksi_Risiko']}%")
            
# --- ROUTER UTAMA ---
if st.session_state.current_page == 'landing':
    landing_page()
elif st.session_state.current_page == 'education':
    education_page()
elif st.session_state.current_page == 'forecast':
    forecast_page()
elif st.session_state.current_page == 'recommendation':
    recommendation_page()