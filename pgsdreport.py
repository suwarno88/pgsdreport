import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os
import json
from openai import OpenAI

# ── Konfigurasi API OpenAI (Backend Secure) ──────────────────────────────────
# Mengambil API key secara aman dari Streamlit Secrets
API_KEY = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else None

# Inisialisasi client OpenAI
client = OpenAI(api_key=API_KEY) if API_KEY else None
OPENAI_MODEL = "gpt-4.1" 

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PGSD Performance Dashboard 2026",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (Dashboard Layout & Glassmorphism Chat) ───────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    border-right: 1px solid rgba(99, 102, 241, 0.2);
}
section[data-testid="stSidebar"] * {
    color: #cbd5e1 !important;
}

.hero-banner {
    background: linear-gradient(135deg, #312e81 0%, #4f46e5 40%, #7c3aed 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(79, 70, 229, 0.3);
}
.hero-banner h1 { color: #ffffff; font-size: 1.9rem; font-weight: 800; margin: 0 0 0.3rem 0; letter-spacing: -0.5px; }
.hero-banner p { color: rgba(255,255,255,0.8); font-size: 1rem; margin: 0; font-weight: 400; }

.kpi-card {
    background: rgba(30, 41, 59, 0.8);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    text-align: center;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}
.kpi-label { color: #94a3b8; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.6rem; }
.kpi-value { color: #f1f5f9; font-size: 2.2rem; font-weight: 800; line-height: 1; margin-bottom: 0.3rem; }
.kpi-sub { font-size: 0.8rem; font-weight: 500; }
.kpi-green { color: #34d399; }
.kpi-yellow { color: #fbbf24; }
.kpi-red { color: #f87171; }
.kpi-blue { color: #60a5fa; }

.section-header {
    color: #e2e8f0; font-size: 1.25rem; font-weight: 700; margin: 1.8rem 0 1rem 0;
    padding-bottom: 0.5rem; border-bottom: 2px solid rgba(99, 102, 241, 0.3);
}

/* Apple Liquid Glassmorphism untuk Native Chat Streamlit */
[data-testid="stChatMessage"] {
    background: rgba(25, 30, 45, 0.4) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 20px !important;
    padding: 1.5rem !important;
    margin-bottom: 1rem !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
}
/* Membedakan warna background untuk chat user */
[data-testid="stChatMessage"]:has([data-testid="stIconUser"]) {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.15)) !important;
    border-left: 4px solid #a855f7 !important;
}
/* Kustomisasi Input Chat Box */
[data-testid="stChatInput"] {
    background: rgba(30, 41, 59, 0.6) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    border-radius: 20px !important;
}
</style>
""", unsafe_allow_html=True)


# ── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    file_path = os.path.join(os.path.dirname(__file__), "ReportRealization_Pendidikan_Guru_Sekolah_Dasar__PGSD_.xlsx")
    try:
        df = pd.read_excel(file_path, header=0)
    except FileNotFoundError:
        st.error("File Excel tidak ditemukan. Pastikan path sesuai.")
        return pd.DataFrame()
        
    df.columns = ["No", "Year", "Performance Indicator", "Unit Name",
                   "Target Q1", "Target Q2", "Target Q3", "Target Q4",
                   "Realization", "Score", "PI Focus"]

    def parse_id_number(val):
        if pd.isna(val): return np.nan
        s = str(val).strip()
        if any(c.isalpha() for c in s.replace("NaN", "")): return np.nan
        try:
            return float(s.replace(".", "").replace(",", "."))
        except:
            return np.nan

    for col in ["Target Q1", "Target Q2", "Target Q3", "Target Q4", "Realization", "Score"]:
        df[col] = df[col].apply(parse_id_number)

    df["No"] = pd.to_numeric(df["No"], errors="coerce").astype("Int64")
    df["PI Focus"] = df["PI Focus"].fillna("NO").astype(str).str.strip().str.upper()
    return df

df = load_data()

# ── Helper Functions ─────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif", color="#cbd5e1"),
    margin=dict(l=40, r=30, t=50, b=40),
    legend=dict(bgcolor="rgba(30,41,59,0.6)", bordercolor="rgba(99,102,241,0.2)", borderwidth=1),
    xaxis=dict(gridcolor="rgba(99,102,241,0.08)", zerolinecolor="rgba(99,102,241,0.15)"),
    yaxis=dict(gridcolor="rgba(99,102,241,0.08)", zerolinecolor="rgba(99,102,241,0.15)"),
)

COLORS = {"primary": "#6366f1", "q1": "#6366f1", "realization": "#22d3ee", "success": "#34d399", "warning": "#fbbf24", "danger": "#f87171"}

def safe_pct(real, target):
    return (real / target) * 100 if (pd.notna(real) and pd.notna(target) and target != 0) else None

def get_achievement_color(pct):
    if pct is None: return "#64748b"
    if pct >= 100: return COLORS["success"]
    if pct >= 75: return COLORS["warning"]
    return COLORS["danger"]


# ── Sidebar & Filters ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 1.5rem 0;">
        <div style="font-size: 2.5rem;">🎓</div>
        <div style="color: #a5b4fc; font-weight: 800; font-size: 1.15rem;">PGSD Dashboard</div>
        <div style="color: #64748b; font-size: 0.75rem;">Performance Indicator 2026</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    selected_quarter = st.selectbox("📅 Pilih Kuartal Perbandingan", ["Q1", "Q2", "Q3", "Q4"], index=3)
    quarter_col = f"Target {selected_quarter}"

    focus_filter = st.radio("🎯 Filter PI Focus", ["Semua", "YES (Fokus)", "NO"], index=0)

    categories = {
        "Semua Kategori": None,
        "🎓 Students & Enrollment": ["Student", "Intake", "Active", "NR Students", "Graduation"],
        "📚 Research & Publication": ["SCOPUS", "Citation", "Research", "publication", "paper", "IP(s)", "MULTIDIS"],
        "📊 Others": None
    }
    selected_category = st.selectbox("📂 Kategori Indikator", list(categories.keys()), index=0)
    
    st.markdown("---")
    
    # Fitur AI Summary di Sidebar
    st.markdown('<div style="color: #a5b4fc; font-weight: 700; margin-bottom: 0.5rem;">✨ AI Data Analysis</div>', unsafe_allow_html=True)
    if st.button("Tuliskan Ringkasan Otomatis", use_container_width=True):
        st.session_state['generate_summary'] = True


# ── Apply Filters ────────────────────────────────────────────────────────────
filtered_df = df.copy()
if focus_filter == "YES (Fokus)": filtered_df = filtered_df[filtered_df["PI Focus"] == "YES"]
elif focus_filter == "NO": filtered_df = filtered_df[filtered_df["PI Focus"] == "NO"]

if selected_category != "Semua Kategori" and selected_category != "📊 Others":
    mask = filtered_df["Performance Indicator"].str.contains("|".join(categories[selected_category]), case=False, na=False)
    filtered_df = filtered_df[mask]

# ── Fitur Generate Summary Otomatis (Backend Secure) ─────────────────────────
if st.session_state.get('generate_summary', False):
    st.markdown("### 🤖 Ringkasan AI Otomatis")
    if not client:
        st.error("Gagal terhubung ke AI: API Key belum dikonfigurasi di Streamlit Secrets.")
    else:
        with st.spinner(f"Menganalisis performa {selected_quarter}..."):
            try:
                # Mengirimkan subset data yang relevan agar konteks tidak melebihi batas token
                summary_data = filtered_df[["Performance Indicator", quarter_col, "Realization", "Score", "PI Focus"]].to_dict(orient="records")
                prompt = f"""Anda adalah analis akademik profesional. Buat ringkasan analitis singkat (maks 3 paragraf, gunakan poin-poin agar rapi) mengenai kinerja PGSD berdasarkan data berikut. Kuartal saat ini adalah {selected_quarter}. 
                Data: {json.dumps(summary_data)}"""
                
                response = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful academic data analyst for the PGSD department. Reply in Indonesian."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5
                )
                st.success(response.choices[0].message.content)
            except Exception as e:
                st.error(f"Terjadi kesalahan saat memproses ringkasan: {e}")
            
        if st.button("Tutup Ringkasan"):
            st.session_state['generate_summary'] = False

# ── Hero Banner & KPIs ──────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-banner">
    <h1>📊 Performance Indicator Dashboard</h1>
    <p>Jurusan Pendidikan Guru Sekolah Dasar (PGSD) — Tahun 2026 &nbsp;|&nbsp;
    Kuartal: <strong>{selected_quarter}</strong></p>
</div>
""", unsafe_allow_html=True)

comparison_df = filtered_df.dropna(subset=[quarter_col, "Realization"]).copy()
comparison_df["Achievement %"] = comparison_df.apply(lambda r: safe_pct(r["Realization"], r[quarter_col]), axis=1)
valid_comp = comparison_df.dropna(subset=["Achievement %"])

achieved_count = len(valid_comp[valid_comp["Achievement %"] >= 100])
avg_ach = valid_comp["Achievement %"].mean() if len(valid_comp) > 0 else 0
avg_color = "kpi-green" if avg_ach >= 100 else ("kpi-yellow" if avg_ach >= 75 else "kpi-red")

col1, col2, col3, col4 = st.columns(4)
with col1: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Indikator</div><div class="kpi-value kpi-blue">{len(filtered_df)}</div></div>', unsafe_allow_html=True)
with col2: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Terukur di {selected_quarter}</div><div class="kpi-value" style="color:#a78bfa;">{len(valid_comp)}</div></div>', unsafe_allow_html=True)
with col3: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Target Tercapai</div><div class="kpi-value kpi-green">{achieved_count}</div></div>', unsafe_allow_html=True)
with col4: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Rata-rata Capaian</div><div class="kpi-value {avg_color}">{avg_ach:.1f}%</div></div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)


# ── Tabs & Charts ────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊 Perbandingan Target", "📈 Analisis Kuartal", "📋 Data Lengkap", "💬 AI Assistant"])

with tab1:
    if len(valid_comp) > 0:
        chart_df = valid_comp.copy()
        chart_df["Short Name"] = chart_df["Performance Indicator"].apply(lambda x: (x[:55]+"…") if len(str(x))>55 else x)

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(y=chart_df["Short Name"], x=chart_df[quarter_col], name=f"Target {selected_quarter}", orientation="h", marker=dict(color=COLORS["q1"])))
        fig_bar.add_trace(go.Bar(y=chart_df["Short Name"], x=chart_df["Realization"], name="Realisasi", orientation="h", marker=dict(color=COLORS["realization"])))
        
        fig_bar.update_layout(
            PLOTLY_LAYOUT, 
            barmode="group", height=max(450, len(chart_df) * 55),
            title=dict(text=f"Target {selected_quarter} vs Realisasi", font=dict(color="#e2e8f0")),
            yaxis=dict(autorange="reversed"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

with tab2:
    st.info("Pilih indikator spesifik untuk melihat analisis kuartalan dan grafik.")
    # (Kode grafik analisis tambahan dari versi Anda sebelumnya bisa diletakkan di sini)

with tab3:
    st.dataframe(filtered_df, use_container_width=True)


# ━━ TAB 4: SECURE AI CHATBOT BACKEND ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab4:
    st.markdown('<div class="section-header">💬 AI Data Assistant</div>', unsafe_allow_html=True)
    st.caption("Tanyakan apa saja mengenai data performa di atas. Asisten ini memproses data secara aman di sisi server dan merender teks dengan rapi.")
    
    # Inisialisasi memori percakapan di Session State
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Halo! Saya AI Assistant khusus Dashboard PGSD. Apa yang ingin Anda analisis dari data indikator hari ini?"}
        ]

    # Render history percakapan menggunakan chat_message bawaan Streamlit
    # Desainnya otomatis mengikuti Apple Liquid Glassmorphism CSS yang disuntikkan di atas
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Kotak Input User
    if prompt := st.chat_input("Contoh: Indikator apa saja yang belum mencapai target?"):
        
        # Tampilkan pesan user di UI
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Simpan pesan user ke history memori
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Ekstrak data saat ini sebagai konteks (agar AI hanya merespons berdasarkan tabel filter saat ini)
        chat_context_data = filtered_df[["Performance Indicator", quarter_col, "Realization", "PI Focus", "Score"]].to_dict(orient="records")
        system_prompt = f"""
        You are an AI data assistant embedded in an academic Performance Dashboard for the PGSD department.
        CRITICAL INSTRUCTIONS:
        1. You MUST ONLY answer questions related to the following JSON data representing the dashboard's current filtered state.
        2. If the user asks anything outside of this data, politely decline and state your purpose.
        3. LANGUAGE MATCHING: Respond in the exact language the user uses (If Indonesian -> Indonesian, If English -> English).
        4. Use Markdown for rich text formatting (bold, italics, bullet points, numbered lists) to make it look professional and neat.
        DASHBOARD DATA:
        {json.dumps(chat_context_data)}
        """

        # Gabungkan system prompt dengan history chat untuk dikirim ke API
        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.messages])

        # Panggil API OpenAI dan tampilkan efek Typewriter
        with st.chat_message("assistant"):
            if not client:
                st.error("⚠️ Koneksi gagal: API Key belum dikonfigurasi di Streamlit Secrets.")
            else:
                try:
                    # Meminta respons dengan stream=True untuk efek mengetik instan
                    stream = client.chat.completions.create(
                        model=OPENAI_MODEL,
                        messages=api_messages,
                        stream=True, 
                    )
                    
                    # st.write_stream akan menampilkan efek typewriter Markdown dengan rapi
                    response_text = st.write_stream(stream)
                    
                    # Simpan respon akhir AI ke history
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat menghubungi API: {e}")
