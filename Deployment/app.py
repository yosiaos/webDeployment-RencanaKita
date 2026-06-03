import streamlit as st
import pandas as pd
import numpy as np
import base64 

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="RencanaKita", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (POPPINS, BG #fdf8f6, TEXT HITAM, FORM PUTIH) ---
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

    /* Terapkan Font Poppins & Background Baru #fdf8f6 */
    html, body, [class*="css"], .stApp {
        font-family: 'Poppins', sans-serif !important;
        background-color: #fdf8f6 !important;
    }
    
    /* Sembunyikan Header/Footer bawaan Streamlit agar bersih */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Semua text menggunakan Poppins dan warna hitam pekat */
    h1, h2, h3, h4, h5, h6,
    p, span, label, li, div, .stMarkdown p, .stMarkdown div,
    .stButton > button, .stFormSubmitButton > button {
        font-family: 'Poppins', sans-serif !important;
        color: #000000 !important;
    }

    /* Memastikan teks label widget input dan dropdown berwarna hitam pekat */
    .stWidget label, .stSelectbox div, .stSlider div, .stNumberInput input {
        color: #000000 !important;
    }

    /* --- BACKGROUND FORM & INPUT JADI PUTIH --- */
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

    /* Tombol Utama */
    div.stButton > button:first-child,
    div.stFormSubmitButton > button:first-child {
        background-color: #da6d51 !important;
        color: #ffffff !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        padding: 0.7rem 1.2rem !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }

    div.stButton > button:first-child:hover,
    div.stFormSubmitButton > button:first-child:hover {
        background-color: #759d4e !important;
        color: #ffffff !important;
    }

    /* --- UPDATE DROPDOWN DENGAN PANAH --- */
    div[data-testid="stSelectbox"] {
        width: fit-content !important;
        min-width: 250px !important;
        position: relative; /* Penting untuk posisi ikon */
    }
    
    div[data-baseweb="select"] > div, 
    div[data-baseweb="select"] {
        background-color: #ffffff !important;
        border: 1px solid #cccccc !important;
    }

    /* Menambahkan ikon panah ke bawah */
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
    
    div[data-baseweb="select"] div[class*="singleValue"] {
        color: #000000 !important;
    }
    
    div[data-baseweb="popover"] ul {
        background-color: #ffffff !important;
    }
    
    div[data-baseweb="popover"] ul li {
        color: #000000 !important;
    }
    
    /* Tabs Navigation */
    .stTabs [data-baseweb="tab"] {
        color: #333333 !important;
        font-weight: 500 !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #da6d51 !important;
        border-bottom-color: #da6d51 !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- FUNGSI NAVIGASI ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'landing'

def navigate_to(page):
    st.session_state.current_page = page

# --- HALAMAN 1: LANDING PAGE ---
def landing_page():
    st.write("<br>", unsafe_allow_html=True)
    col_kiri, col_kanan = st.columns([1.2, 1], gap="large")
    
    with col_kiri:
        st.markdown("<h2> </h2>", unsafe_allow_html=True)
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
            
            # Konversi video ke base64
            import base64
            
            def get_base64_video(path):
                with open(path, "rb") as file:
                    video_bytes = file.read()
                return base64.b64encode(video_bytes).decode()

            # Panggil fungsi ini (pastikan path ke logo.mp4 benar)
            video_base64 = get_base64_video("Logo/logo.mp4")
            
            # HTML Video tanpa kontrol sama sekali
            video_html = f"""
            <div style="display: flex; justify-content: center; align-items: center; height: 100%; pointer-events: none;">
                <video width="100%" autoplay loop muted playsinline style="border-radius: 24px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">
                    <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
                </video>
            </div>
            """
            st.markdown(video_html, unsafe_allow_html=True)

# --- HALAMAN 2: EDUCATION ---
def education_page():
    st.button("Kembali ke Beranda", on_click=navigate_to, args=('landing',))
    st.title("Pusat Edukasi Investasi")
    st.markdown("Pelajari istilah fundamental dan berbagai instrumen investasi sebelum memulai.")
    st.write("---")
    
    tab_fondasi, tab_instrumen = st.tabs(["Fondasi Fundamental", "Instrumen Investasi"])
    
    with tab_fondasi:
        st.subheader("Kosakata Fundamental")
        st.info("Silakan tambahkan kosakata investasi di sini secara mandiri.")
        st.markdown("- **Diversifikasi:** Strategi menyebar dana investasi ke berbagai aset untuk mengurangi risiko.")
        st.markdown("- **Return:** Hasil yang diperoleh dari penanaman modal.")
        st.markdown("- **Risk Tolerance:** Tingkat ketidakpastian yang berani diambil investor.")
        
    with tab_instrumen:
        t_dep, t_rek, t_obl, t_emas, t_sah = st.tabs(["Deposito", "Reksadana", "Obligasi", "Emas", "Saham"])
        
        with t_dep: st.write("Penjelasan mengenai Deposito...")
        with t_rek: st.write("Penjelasan mengenai Reksadana...")
        with t_obl: st.write("Penjelasan mengenai Obligasi...")
        with t_emas: st.write("Penjelasan mengenai Emas...")
        with t_sah:
            st.write("Jelajahi Emiten Saham:")
            saham_list = [
                "ADRO", "ANTM", "ASII", "BBCA", "BBNI", "BBRI", "BMRI", 
                "CUAN", "ICBP", "INCO", "ISAT", "MEDC", "MYOR", "PTBA", "TLKM"
            ]
            selected_saham = st.selectbox("Pilih Emiten untuk melihat detail:", saham_list)
            
            with st.container():
                st.markdown(f"### **{selected_saham}**")
                st.write(f"Berikut adalah deskripsi dan fundamental bisnis terkait emiten **{selected_saham}** yang akan ditampilkan secara dinamis.")

# --- HALAMAN 3: FORECAST ---
def forecast_page():
    st.button("Kembali ke Beranda", on_click=navigate_to, args=('landing',))
    st.title("Visualisasi Forecast")
    st.markdown("Prediksi pergerakan instrumen selama 90 hari ke depan.")
    
    assets = [
        "Emas", "ADRO", "ANTM", "ASII", "BBCA", "BBNI", "BBRI", "BMRI", 
        "CUAN", "ICBP", "INCO", "ISAT", "MEDC", "MYOR", "PTBA", "TLKM"
    ]
    selected_asset = st.selectbox("Pilih Instrumen:", assets)
    st.write("---")
    
    col_img, col_text = st.columns([1.5, 1], gap="large")
    with col_img:
        st.markdown(f"**Grafik Prediksi 90 Hari - {selected_asset}**")
        st.markdown(
            "<div style='height:350px; background-color:#ffffff; border: 1px solid #e0e0e0; border-radius:12px; display:flex; align-items:center; justify-content:center;'>"
            "<p style='color:#da6d51; font-weight:bold;'>[ MASUKIN GAMBAR FORECAST DI SINI ]</p>"
            "</div>", 
            unsafe_allow_html=True
        )
        
    with col_text:
        st.markdown("**Insight & Deskripsi**")
        with st.container(border=True):
            st.markdown(f"**Brief Market Analysis:**")
            st.write(f"- Prediksi menunjukkan tren pergerakan untuk komponen {selected_asset}.")
            st.write("- **Level Support:** Rp ...")
            st.write("- **Level Resistance:** Rp ...")
            st.info("Insight ini akan di-generate otomatis oleh model setelah deployment penuh.")

# --- HALAMAN 4: RECOMMENDATION ---
def recommendation_page():
    st.button("Kembali ke Beranda", on_click=navigate_to, args=('landing',))
    st.title("Rekomendasi Portofolio")
    st.markdown("Masukkan profil finansial Anda untuk mendapatkan rekomendasi alokasi investasi yang dipersonalisasi.")
    
    # Form Container akan berwarna putih karena CSS [data-testid="stForm"]
    with st.form("recommendation_form", border=True):
        st.subheader("Profil Finansial Anda")
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            age = st.number_input("Umur (Tahun)", min_value=17, max_value=100, step=1, value=25)
            monthly_income = st.number_input("Pendapatan Bulanan (Rp)", min_value=1_000_000, value=10_000_000, step=500_000)
            investment_horizon = st.slider("Horizon Investasi (Tahun)", min_value=1, max_value=20, value=5)
            
        with col2:
            risk_tolerance = st.slider("Toleransi Risiko (1=Konservatif, 10=Agresif)", 1, 10, 5)
            investment_goal = st.selectbox("Tujuan Investasi", [
                "Retirement", 
                "Education", 
                "Emergency Fund", 
                "Wealth Growth",
                "Lainnya"
            ])
            
        st.write("")
        submit = st.form_submit_button("Generate Rekomendasi Portofolio")
        
    if submit:
        st.success("Data berhasil diproses oleh Model Inference.")
        st.markdown("### Hasil Rekomendasi Alokasi")
        
        with st.container(border=True):
            if risk_tolerance >= 7:
                st.markdown("#### Profil: **Aggressive Growth**")
                st.progress(60, text="Saham: 60%")
                st.progress(20, text="Emas: 20%")
                st.progress(20, text="Reksadana: 20%")
            elif risk_tolerance <= 4:
                st.markdown("#### Profil: **Conservative**")
                st.progress(40, text="Deposito: 40%")
                st.progress(40, text="Obligasi: 40%")
                st.progress(20, text="Reksadana: 20%")
            else:
                st.markdown("#### Profil: **Moderate**")
                st.progress(40, text="Reksadana: 40%")
                st.progress(30, text="Obligasi: 30%")
                st.progress(20, text="Saham: 20%")
                st.progress(10, text="Emas: 10%")

# --- ROUTER UTAMA ---
if st.session_state.current_page == 'landing':
    landing_page()
elif st.session_state.current_page == 'education':
    education_page()
elif st.session_state.current_page == 'forecast':
    forecast_page()
elif st.session_state.current_page == 'recommendation':
    recommendation_page()   