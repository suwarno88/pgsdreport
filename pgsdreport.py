import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import json
import os
import requests
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import streamlit.components.v1 as components

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ── INTERNAL API PROXY SERVER (Production-Safe) ──────────────────────────────
# API key stays on the server. JS chatbot calls this proxy, NOT OpenAI direct.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _get_secret(key, fallback=""):
    """Read from st.secrets → env var → fallback."""
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, fallback)

# ── Globals set once at import time ──────────────────────────────────────────
_OPENAI_API_KEY = _get_secret("OPENAI_API_KEY")
_OPENAI_ENDPOINT = _get_secret("OPENAI_ENDPOINT", "https://api.openai.com/v1/chat/completions")
_OPENAI_MODEL = _get_secret("OPENAI_MODEL", "gpt-4.1")
_DATA_CONTEXT_GLOBAL = ""  # filled after data loads


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class _ChatProxyHandler(BaseHTTPRequestHandler):
    """Lightweight HTTP handler — proxies chat requests to OpenAI."""

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_response(404)
            self._cors()
            self.end_headers()
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            messages = body.get("messages", [])

            resp = requests.post(
                _OPENAI_ENDPOINT,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {_OPENAI_API_KEY}",
                },
                json={
                    "model": _OPENAI_MODEL,
                    "messages": messages,
                    "max_tokens": 1500,
                    "temperature": 0.7,
                },
                timeout=90,
            )

            self.send_response(resp.status_code)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(resp.content)

        except Exception as exc:
            self.send_response(502)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": {"message": str(exc)}}).encode())

    # ── helpers ──
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, _fmt, *_args):
        pass  # silence stdout


# Start proxy once per process (Streamlit re-runs the script on interaction,
# but module-level code runs only on first import).
if "proxy_port" not in st.session_state:
    _port = _find_free_port()
    _server = HTTPServer(("0.0.0.0", _port), _ChatProxyHandler)
    threading.Thread(target=_server.serve_forever, daemon=True).start()
    st.session_state["proxy_port"] = _port

PROXY_PORT = st.session_state["proxy_port"]


# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PGSD Performance Dashboard 2026",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%); }
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    border-right: 1px solid rgba(99,102,241,0.2);
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] label { color: #cbd5e1 !important; }

.hero-banner {
    background: linear-gradient(135deg, #312e81 0%, #4f46e5 40%, #7c3aed 100%);
    border-radius: 16px; padding: 2rem 2.5rem; margin-bottom: 1.5rem;
    position: relative; overflow: hidden; box-shadow: 0 20px 60px rgba(79,70,229,0.3);
}
.hero-banner::before {
    content:''; position:absolute; top:-50%; right:-20%; width:400px; height:400px;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%); border-radius:50%;
}
.hero-banner h1 { color:#fff; font-size:1.9rem; font-weight:800; margin:0 0 .3rem 0; letter-spacing:-.5px; }
.hero-banner p { color:rgba(255,255,255,.8); font-size:1rem; margin:0; font-weight:400; }

.kpi-card {
    background:rgba(30,41,59,.8); backdrop-filter:blur(10px);
    border:1px solid rgba(99,102,241,.15); border-radius:14px;
    padding:1.4rem 1.6rem; text-align:center; transition:all .3s ease;
    box-shadow:0 4px 20px rgba(0,0,0,.2);
}
.kpi-card:hover { border-color:rgba(99,102,241,.5); transform:translateY(-2px); box-shadow:0 8px 30px rgba(99,102,241,.15); }
.kpi-label { color:#94a3b8; font-size:.78rem; font-weight:600; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:.6rem; }
.kpi-value { color:#f1f5f9; font-size:2.2rem; font-weight:800; line-height:1; margin-bottom:.3rem; }
.kpi-sub { font-size:.8rem; font-weight:500; }
.kpi-green{color:#34d399;} .kpi-yellow{color:#fbbf24;} .kpi-red{color:#f87171;} .kpi-blue{color:#60a5fa;}

.section-header {
    color:#e2e8f0; font-size:1.25rem; font-weight:700; margin:1.8rem 0 1rem 0;
    padding-bottom:.5rem; border-bottom:2px solid rgba(99,102,241,.3);
    display:flex; align-items:center; gap:.5rem;
}

div[data-testid="stMetric"] { background:rgba(30,41,59,.8); border:1px solid rgba(99,102,241,.15); border-radius:14px; padding:1rem 1.2rem; }
.stTabs [data-baseweb="tab-list"] { gap:8px; background:transparent; }
.stTabs [data-baseweb="tab"] { background:rgba(30,41,59,.6); border-radius:10px 10px 0 0; border:1px solid rgba(99,102,241,.15); color:#94a3b8; font-weight:600; padding:.6rem 1.2rem; }
.stTabs [aria-selected="true"] { background:rgba(79,70,229,.2)!important; border-color:rgba(99,102,241,.4)!important; color:#a5b4fc!important; }
div[data-testid="stExpander"] { background:rgba(30,41,59,.5); border:1px solid rgba(99,102,241,.1); border-radius:12px; }
.stSelectbox label,.stMultiSelect label,.stRadio label { color:#cbd5e1!important; font-weight:600!important; }
</style>
""", unsafe_allow_html=True)


# ── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    file_path = os.path.join(os.path.dirname(__file__),
                             "ReportRealization_Pendidikan_Guru_Sekolah_Dasar__PGSD_.xlsx")
    df = pd.read_excel(file_path, header=0)
    df.columns = ["No","Year","Performance Indicator","Unit Name",
                   "Target Q1","Target Q2","Target Q3","Target Q4",
                   "Realization","Score","PI Focus"]

    def parse_id_number(val):
        if pd.isna(val): return np.nan
        s = str(val).strip()
        if any(c.isalpha() for c in s.replace("NaN","")): return np.nan
        try:
            s = s.replace(".","").replace(",",".")
            return float(s)
        except (ValueError, TypeError):
            return np.nan

    for col in ["Target Q1","Target Q2","Target Q3","Target Q4","Realization","Score"]:
        df[col] = df[col].apply(parse_id_number)
    df["No"] = pd.to_numeric(df["No"], errors="coerce").astype("Int64")
    df["PI Focus"] = df["PI Focus"].fillna("NO").astype(str).str.strip().str.upper()
    return df


df = load_data()


# ── Build data context for AI ────────────────────────────────────────────────
@st.cache_data
def build_data_context(_df):
    lines = ["=== DATA PERFORMANCE INDICATOR PGSD 2026 ===",
             "Jurusan: Pendidikan Guru Sekolah Dasar (PGSD)",
             f"Tahun: 2026 | Total Indikator: {len(_df)}",
             f"PI Focus (Prioritas Tinggi): {len(_df[_df['PI Focus']=='YES'])} indikator\n"]
    for _, r in _df.iterrows():
        no = int(r['No']) if pd.notna(r['No']) else '?'
        tq = [f"Q{i+1}:{r[f'Target Q{i+1}']:,.2f}" if pd.notna(r[f'Target Q{i+1}']) else f"Q{i+1}:N/A" for i in range(4)]
        real = f"{r['Realization']:,.2f}" if pd.notna(r['Realization']) else 'N/A'
        sc = f"{r['Score']:,.2f}" if pd.notna(r['Score']) else 'N/A'
        ach = ''
        if pd.notna(r['Realization']) and pd.notna(r['Target Q4']) and r['Target Q4']!=0:
            ach = f", AchQ4:{r['Realization']/r['Target Q4']*100:.1f}%"
        lines.append(f"#{no}. {r['Performance Indicator']} | {', '.join(tq)} | Real:{real} | Skor:{sc} | Focus:{r['PI Focus']}{ach}")
    return "\n".join(lines)


data_context = build_data_context(df)
_DATA_CONTEXT_GLOBAL = data_context  # expose to proxy


# ── Plotly + Helpers ─────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif", color="#cbd5e1"),
    margin=dict(l=40, r=30, t=50, b=40),
    legend=dict(bgcolor="rgba(30,41,59,0.6)", bordercolor="rgba(99,102,241,0.2)",
                borderwidth=1, font=dict(size=11)),
    xaxis=dict(gridcolor="rgba(99,102,241,0.08)", zerolinecolor="rgba(99,102,241,0.15)"),
    yaxis=dict(gridcolor="rgba(99,102,241,0.08)", zerolinecolor="rgba(99,102,241,0.15)"),
)

COLORS = {
    "primary":"#6366f1","secondary":"#a78bfa","accent":"#22d3ee",
    "success":"#34d399","warning":"#fbbf24","danger":"#f87171",
    "q1":"#6366f1","realization":"#22d3ee",
}

def safe_pct(real, target):
    if pd.isna(real) or pd.isna(target) or target==0: return None
    return (real/target)*100

def ach_color(pct):
    if pct is None: return "#64748b"
    if pct>=100: return COLORS["success"]
    if pct>=75: return COLORS["warning"]
    return COLORS["danger"]

def ach_label(pct):
    if pct is None: return "N/A"
    if pct>=100: return "✅ Achieved"
    if pct>=75: return "⚠️ On Track"
    return "❌ Below Target"


def call_openai(system_prompt, user_content, max_tokens=3000):
    """Server-side OpenAI call using secrets."""
    resp = requests.post(
        _OPENAI_ENDPOINT,
        headers={"Content-Type":"application/json","Authorization":f"Bearer {_OPENAI_API_KEY}"},
        json={"model":_OPENAI_MODEL,
              "messages":[{"role":"system","content":system_prompt},
                          {"role":"user","content":user_content}],
              "max_tokens":max_tokens,"temperature":0.7},
        timeout=90,
    )
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    raise RuntimeError(f"OpenAI API {resp.status_code}: {resp.text[:300]}")


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:1rem 0 1.5rem 0;">
        <div style="font-size:2.5rem; margin-bottom:.3rem;">🎓</div>
        <div style="color:#a5b4fc; font-weight:800; font-size:1.15rem;">PGSD Dashboard</div>
        <div style="color:#64748b; font-size:.75rem; font-weight:500;">Performance Indicator 2026</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    selected_quarter = st.selectbox("📅 Pilih Kuartal", ["Q1","Q2","Q3","Q4"], index=3)
    quarter_col = f"Target {selected_quarter}"
    focus_filter = st.radio("🎯 Filter PI Focus", ["Semua","YES (Fokus)","NO"], index=0)
    categories = {
        "Semua Kategori": None,
        "🎓 Students & Enrollment": ["Student","Intake","Active","NR Students","Graduation"],
        "💰 Revenue & Finance": ["Revenue","revenue"],
        "🤝 Partnership": ["Partnership","partner"],
        "📚 Research & Publication": ["SCOPUS","Citation","Research","publication","paper","IP(s)","MULTIDIS"],
        "🌐 International": ["International","Inbound","Outbound"],
        "👩‍🏫 Employment & Career": ["Employment","Entrepreneur","Employability"],
        "📊 Others": None,
    }
    selected_category = st.selectbox("📂 Kategori", list(categories.keys()), index=0)
    st.markdown("---")
    st.markdown("""
    <div style="padding:.8rem; background:rgba(99,102,241,.08); border-radius:10px;
                border:1px solid rgba(99,102,241,.15); margin-top:.5rem;">
        <div style="color:#a5b4fc; font-weight:700; font-size:.82rem; margin-bottom:.5rem;">ℹ️ Petunjuk</div>
        <div style="color:#94a3b8; font-size:.74rem; line-height:1.5;">
            • Pilih kuartal untuk perbandingan target vs realisasi<br>
            • Klik 💬 di pojok kanan bawah untuk AI Chatbot<br>
            • Tab "AI Summary" untuk ringkasan otomatis
        </div>
    </div>""", unsafe_allow_html=True)


# ── Apply Filters ────────────────────────────────────────────────────────────
filtered_df = df.copy()
if focus_filter=="YES (Fokus)":
    filtered_df = filtered_df[filtered_df["PI Focus"]=="YES"]
elif focus_filter=="NO":
    filtered_df = filtered_df[filtered_df["PI Focus"]=="NO"]

if selected_category not in ("Semua Kategori","📊 Others"):
    kw = categories[selected_category]
    if kw: filtered_df = filtered_df[filtered_df["Performance Indicator"].str.contains("|".join(kw), case=False, na=False)]
elif selected_category=="📊 Others":
    all_kw = [w for v in categories.values() if v for w in v]
    filtered_df = filtered_df[~filtered_df["Performance Indicator"].str.contains("|".join(all_kw), case=False, na=False)]


# ── Hero Banner ──────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-banner">
    <h1>📊 Performance Indicator Dashboard</h1>
    <p>Jurusan Pendidikan Guru Sekolah Dasar (PGSD) — Tahun 2026 &nbsp;|&nbsp;
    Kuartal: <strong>{selected_quarter}</strong> &nbsp;|&nbsp;
    <strong>{len(filtered_df)}</strong>/{len(df)} indikator</p>
</div>""", unsafe_allow_html=True)


# ── KPI Cards ────────────────────────────────────────────────────────────────
comp_df = filtered_df.dropna(subset=[quarter_col,"Realization"]).copy()
comp_df["Ach%"] = comp_df.apply(lambda r: safe_pct(r["Realization"], r[quarter_col]), axis=1)
valid_comp = comp_df.dropna(subset=["Ach%"])
total_ind = len(filtered_df)
measurable = len(valid_comp)
achieved_n = len(valid_comp[valid_comp["Ach%"]>=100]) if len(valid_comp)>0 else 0
avg_ach = valid_comp["Ach%"].mean() if len(valid_comp)>0 else 0
pi_n = len(filtered_df[filtered_df["PI Focus"]=="YES"])
avg_cls = "kpi-green" if avg_ach>=100 else ("kpi-yellow" if avg_ach>=75 else "kpi-red")

c1,c2,c3,c4,c5 = st.columns(5)
with c1: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Indikator</div><div class="kpi-value kpi-blue">{total_ind}</div><div class="kpi-sub" style="color:#64748b;">ditampilkan</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Terukur ({selected_quarter})</div><div class="kpi-value" style="color:#a78bfa;">{measurable}</div><div class="kpi-sub" style="color:#64748b;">target & realisasi</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Tercapai</div><div class="kpi-value kpi-green">{achieved_n}</div><div class="kpi-sub kpi-green">≥ 100%</div></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Rata-rata Capaian</div><div class="kpi-value {avg_cls}">{avg_ach:.1f}%</div><div class="kpi-sub" style="color:#64748b;">target {selected_quarter}</div></div>', unsafe_allow_html=True)
with c5: st.markdown(f'<div class="kpi-card"><div class="kpi-label">PI Focus</div><div class="kpi-value" style="color:#fbbf24;">{pi_n}</div><div class="kpi-sub" style="color:#64748b;">prioritas tinggi</div></div>', unsafe_allow_html=True)
st.markdown("<div style='height:.8rem;'></div>", unsafe_allow_html=True)


# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5 = st.tabs(["📊 Target vs Realisasi","📈 Analisis Kuartal","🎯 PI Focus","📋 Data Lengkap","🤖 AI Summary"])

# ━━ TAB 1 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    st.markdown(f'<div class="section-header">📊 Target {selected_quarter} vs Realisasi</div>', unsafe_allow_html=True)
    if len(valid_comp)==0:
        st.warning(f"Tidak ada data perbandingan untuk {selected_quarter}.")
    else:
        cdf = valid_comp.copy()
        cdf["SN"] = cdf["Performance Indicator"].apply(lambda x: (x[:55]+"…") if len(str(x))>55 else x)
        fig = go.Figure()
        fig.add_trace(go.Bar(y=cdf["SN"], x=cdf[quarter_col], name=f"Target {selected_quarter}",
                             orientation="h", marker=dict(color=COLORS["q1"]), opacity=0.85,
                             text=cdf[quarter_col].apply(lambda v: f"{v:,.2f}"), textposition="auto", textfont=dict(size=10)))
        fig.add_trace(go.Bar(y=cdf["SN"], x=cdf["Realization"], name="Realisasi",
                             orientation="h", marker=dict(color=COLORS["realization"]), opacity=0.85,
                             text=cdf["Realization"].apply(lambda v: f"{v:,.2f}"), textposition="auto", textfont=dict(size=10)))
        fig.update_layout(PLOTLY_LAYOUT, barmode="group", height=max(450, len(cdf)*55),
                          title=dict(text=f"Target {selected_quarter} vs Realisasi", font=dict(size=16, color="#e2e8f0")),
                          yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f'<div class="section-header">🏆 Persentase Capaian ({selected_quarter})</div>', unsafe_allow_html=True)
        cds = cdf.sort_values("Ach%", ascending=True)
        fig2 = go.Figure(go.Bar(y=cds["SN"], x=cds["Ach%"], orientation="h",
                                marker=dict(color=[ach_color(v) for v in cds["Ach%"]]),
                                text=cds["Ach%"].apply(lambda v: f"{v:.1f}%"),
                                textposition="outside", textfont=dict(size=10, color="#e2e8f0")))
        fig2.add_vline(x=100, line_dash="dash", line_color="#fbbf24", line_width=1.5,
                       annotation_text="100%", annotation_font=dict(color="#fbbf24", size=10))
        fig2.update_layout(PLOTLY_LAYOUT, height=max(450, len(cds)*50),
                           title=dict(text="Achievement Rate (%)", font=dict(size=16, color="#e2e8f0")),
                           xaxis=dict(title="Achievement %", range=[0, max(cds["Ach%"].max()*1.2, 120)]),
                           yaxis=dict(tickfont=dict(size=10)), showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)


# ━━ TAB 2 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    st.markdown('<div class="section-header">📈 Tren Target per Kuartal</div>', unsafe_allow_html=True)
    opts = filtered_df["Performance Indicator"].tolist()
    sel_ind = st.multiselect("Pilih indikator:", opts, default=opts[:5] if len(opts)>=5 else opts)
    if sel_ind:
        sdf = filtered_df[filtered_df["Performance Indicator"].isin(sel_ind)].copy()
        q_cols = ["Target Q1","Target Q2","Target Q3","Target Q4"]
        avail = [c for c in q_cols if sdf[c].notna().any()]
        if avail:
            melt = sdf.melt(id_vars=["No","Performance Indicator","Realization"], value_vars=avail,
                            var_name="Quarter", value_name="Target Value").dropna(subset=["Target Value"])
            melt["QL"] = melt["Quarter"].str.replace("Target ","")
            melt["SN"] = melt["Performance Indicator"].apply(lambda x: (x[:50]+"…") if len(str(x))>50 else x)
            fig = px.line(melt, x="QL", y="Target Value", color="SN", markers=True,
                          color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_traces(line=dict(width=2.5), marker=dict(size=8))
            fig.update_layout(PLOTLY_LAYOUT, height=500,
                              title=dict(text="Tren Target Q1→Q4", font=dict(size=16, color="#e2e8f0")),
                              xaxis_title="Kuartal", yaxis_title="Nilai Target",
                              legend=dict(orientation="h", yanchor="top", y=-0.15, font=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True)

            st.markdown('<div class="section-header">🕸️ Radar: Target Q4 vs Realisasi</div>', unsafe_allow_html=True)
            rdf = sdf.dropna(subset=["Target Q4","Realization"]).copy()
            if len(rdf)>=3:
                rdf["SN"] = rdf["Performance Indicator"].apply(lambda x: (x[:35]+"…") if len(str(x))>35 else x)
                mx = rdf[["Target Q4","Realization"]].max().max()
                if mx>0:
                    rdf["Tn"] = rdf["Target Q4"]/mx*100; rdf["Rn"] = rdf["Realization"]/mx*100
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(r=rdf["Tn"].tolist()+[rdf["Tn"].iloc[0]],
                        theta=rdf["SN"].tolist()+[rdf["SN"].iloc[0]], fill="toself", name="Target Q4",
                        line=dict(color=COLORS["primary"], width=2), fillcolor="rgba(99,102,241,0.15)"))
                    fig.add_trace(go.Scatterpolar(r=rdf["Rn"].tolist()+[rdf["Rn"].iloc[0]],
                        theta=rdf["SN"].tolist()+[rdf["SN"].iloc[0]], fill="toself", name="Realisasi",
                        line=dict(color=COLORS["realization"], width=2), fillcolor="rgba(34,211,238,0.12)"))
                    fig.update_layout(PLOTLY_LAYOUT, height=500,
                        polar=dict(bgcolor="rgba(0,0,0,0)",
                                   radialaxis=dict(visible=True, gridcolor="rgba(99,102,241,0.1)", color="#64748b"),
                                   angularaxis=dict(gridcolor="rgba(99,102,241,0.1)", color="#94a3b8", tickfont=dict(size=9))),
                        title=dict(text="Radar Comparison (Normalized)", font=dict(size=16, color="#e2e8f0")))
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Pilih minimal 3 indikator dengan Target Q4 dan Realisasi.")
        else:
            st.info("Tidak ada target kuartal numerik.")
    else:
        st.info("Pilih minimal satu indikator.")

    st.markdown('<div class="section-header">📊 Distribusi Skor</div>', unsafe_allow_html=True)
    scdf = filtered_df.dropna(subset=["Score"])
    if len(scdf)>0:
        fig = px.histogram(scdf, x="Score", nbins=10, color_discrete_sequence=[COLORS["secondary"]])
        fig.update_layout(PLOTLY_LAYOUT, height=350,
                          title=dict(text="Distribusi Skor", font=dict(size=15, color="#e2e8f0")), bargap=0.1)
        fig.update_traces(marker_line_width=0, opacity=0.85)
        st.plotly_chart(fig, use_container_width=True)


# ━━ TAB 3 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    st.markdown('<div class="section-header">🎯 Indikator PI Focus</div>', unsafe_allow_html=True)
    fdf = df[df["PI Focus"]=="YES"].copy()
    if len(fdf)==0:
        st.info("Tidak ada indikator PI Focus.")
    else:
        for _, row in fdf.iterrows():
            tv=row[quarter_col]; rv=row["Realization"]; pct=safe_pct(rv,tv)
            col=ach_color(pct); lbl=ach_label(pct)
            pt=f"{pct:.1f}%" if pct else "N/A"
            tt=f"{tv:,.2f}" if pd.notna(tv) else "—"
            rt=f"{rv:,.2f}" if pd.notna(rv) else "—"
            sc=f"{row['Score']:,.2f}" if pd.notna(row['Score']) else "—"
            st.markdown(f"""
            <div style="background:rgba(30,41,59,.7);border:1px solid rgba(99,102,241,.15);
                        border-left:4px solid {col};border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:.8rem;
                        box-shadow:0 4px 15px rgba(0,0,0,.15);">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:.8rem;">
                    <div style="flex:1;min-width:250px;">
                        <div style="color:#e2e8f0;font-weight:700;font-size:.95rem;margin-bottom:.4rem;">
                            #{int(row['No'])} — {row['Performance Indicator']}</div>
                        <div style="color:#64748b;font-size:.78rem;">Skor: {sc}</div>
                    </div>
                    <div style="display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap;">
                        <div style="text-align:center;"><div style="color:#64748b;font-size:.7rem;text-transform:uppercase;">Target {selected_quarter}</div><div style="color:#a5b4fc;font-size:1.1rem;font-weight:700;">{tt}</div></div>
                        <div style="text-align:center;"><div style="color:#64748b;font-size:.7rem;text-transform:uppercase;">Realisasi</div><div style="color:#22d3ee;font-size:1.1rem;font-weight:700;">{rt}</div></div>
                        <div style="text-align:center;"><div style="color:#64748b;font-size:.7rem;text-transform:uppercase;">Capaian</div><div style="color:{col};font-size:1.1rem;font-weight:700;">{pt}</div></div>
                        <div style="font-size:.82rem;">{lbl}</div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        fc=fdf.copy(); fc["Ach"]=fc.apply(lambda r: safe_pct(r["Realization"],r[quarter_col]),axis=1)
        fv=fc.dropna(subset=["Ach"])
        if len(fv)>0:
            a=len(fv[fv["Ach"]>=100]); na=len(fv)-a; nd=len(fc)-len(fv)
            fig=go.Figure(go.Pie(labels=["Tercapai ≥100%","Belum Tercapai","Belum Tersedia"],
                values=[a,na,nd],hole=0.6,
                marker=dict(colors=[COLORS["success"],COLORS["danger"],"#475569"],line=dict(width=2,color="#1e293b")),
                textinfo="label+value",textfont=dict(size=12)))
            fig.update_layout(PLOTLY_LAYOUT, height=400,
                title=dict(text=f"Status PI Focus — {selected_quarter}", font=dict(size=16,color="#e2e8f0")),
                annotations=[dict(text=f"{a}/{len(fc)}",x=0.5,y=0.5,
                    font=dict(size=28,color="#e2e8f0",family="Plus Jakarta Sans"),showarrow=False)])
            st.plotly_chart(fig, use_container_width=True)


# ━━ TAB 4 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab4:
    st.markdown('<div class="section-header">📋 Tabel Data Lengkap</div>', unsafe_allow_html=True)
    ddf=filtered_df.copy()
    ddf["Achievement %"]=ddf.apply(lambda r: safe_pct(r["Realization"],r[quarter_col]),axis=1)
    ddf["Status"]=ddf["Achievement %"].apply(ach_label)
    search=st.text_input("🔍 Cari indikator...", placeholder="Ketik kata kunci...")
    if search:
        ddf=ddf[ddf["Performance Indicator"].str.contains(search, case=False, na=False)]
    st.markdown(f"Menampilkan **{len(ddf)}** indikator")
    cols=["No","Performance Indicator","Target Q1","Target Q2","Target Q3","Target Q4","Realization","Score","PI Focus","Achievement %","Status"]
    st.dataframe(
        ddf[cols].style.format({
            "Target Q1":lambda v:f"{v:,.2f}" if pd.notna(v) else "—",
            "Target Q2":lambda v:f"{v:,.2f}" if pd.notna(v) else "—",
            "Target Q3":lambda v:f"{v:,.2f}" if pd.notna(v) else "—",
            "Target Q4":lambda v:f"{v:,.2f}" if pd.notna(v) else "—",
            "Realization":lambda v:f"{v:,.2f}" if pd.notna(v) else "—",
            "Score":lambda v:f"{v:,.2f}" if pd.notna(v) else "—",
            "Achievement %":lambda v:f"{v:.1f}%" if pd.notna(v) else "—",
        }).applymap(lambda v:"color:#34d399" if v=="✅ Achieved" else ("color:#fbbf24" if v=="⚠️ On Track" else ("color:#f87171" if v=="❌ Below Target" else "")), subset=["Status"]),
        use_container_width=True, height=600)
    st.download_button("⬇️ Download CSV", filtered_df.to_csv(index=False).encode("utf-8"),
                       "pgsd_performance_2026.csv","text/csv")


# ━━ TAB 5: AI Summary ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab5:
    st.markdown('<div class="section-header">🤖 AI-Generated Summary</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#94a3b8;font-size:.88rem;margin-bottom:1rem;">Klik tombol untuk ringkasan analitis otomatis menggunakan AI.</div>', unsafe_allow_html=True)
    slang = st.selectbox("🌐 Bahasa Summary", ["Bahasa Indonesia","English"], index=0, key="slang")
    if st.button("✨ Generate AI Summary", type="primary", use_container_width=True):
        with st.spinner("🔄 AI sedang menganalisis data..."):
            lang = "Jawab dalam Bahasa Indonesia." if slang=="Bahasa Indonesia" else "Answer in English."
            sys_prompt = f"""Anda adalah analis data Performance Indicator PGSD 2026. {lang}
Buatlah ringkasan analitis komprehensif:
1. **Overview** - Gambaran umum performa
2. **Indikator Tercapai** - Yang sudah mencapai target
3. **Indikator Perlu Perhatian** - Yang masih jauh dari target
4. **PI Focus Analysis** - Analisis prioritas tinggi
5. **Rekomendasi** - Saran strategis
Gunakan markdown (heading, bold, bullet) agar mudah dibaca."""
            try:
                summary = call_openai(sys_prompt, data_context)
                st.markdown(summary)
            except Exception as e:
                st.error(f"Error: {e}")


# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;padding:1rem 0 .5rem 0;">
    <div style="color:#475569;font-size:.78rem;font-weight:500;">
        🎓 PGSD Performance Dashboard 2026 &nbsp;|&nbsp; Streamlit & Plotly &nbsp;|&nbsp; Powered by OpenAI
    </div>
</div>""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ── FLOATING CHATBOT (Glassmorphism) ─────────────────────────────────────────
# JS calls the internal Python proxy — API key NEVER reaches the browser.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

data_ctx_js = json.dumps(data_context)

chatbot_html = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

#cb-toggle {{
    position:fixed; bottom:28px; right:28px; z-index:99999;
    width:60px; height:60px; border-radius:50%;
    border:1px solid rgba(255,255,255,.25);
    background:linear-gradient(135deg,rgba(99,102,241,.7),rgba(139,92,246,.6),rgba(34,211,238,.5));
    backdrop-filter:blur(20px) saturate(180%);
    -webkit-backdrop-filter:blur(20px) saturate(180%);
    box-shadow:0 8px 32px rgba(99,102,241,.4),inset 0 1px 0 rgba(255,255,255,.3);
    cursor:pointer; display:flex; align-items:center; justify-content:center;
    transition:all .4s cubic-bezier(.34,1.56,.64,1);
    animation:cb-pulse 3s ease-in-out infinite;
}}
#cb-toggle:hover {{ transform:scale(1.1); box-shadow:0 12px 40px rgba(99,102,241,.5),inset 0 1px 0 rgba(255,255,255,.4); }}
#cb-toggle svg {{ width:28px; height:28px; fill:white; filter:drop-shadow(0 1px 2px rgba(0,0,0,.2)); transition:transform .3s ease; }}
#cb-toggle.active svg {{ transform:rotate(90deg); }}
@keyframes cb-pulse {{
    0%,100% {{ box-shadow:0 8px 32px rgba(99,102,241,.4),inset 0 1px 0 rgba(255,255,255,.3); }}
    50% {{ box-shadow:0 8px 40px rgba(99,102,241,.6),0 0 20px rgba(139,92,246,.3),inset 0 1px 0 rgba(255,255,255,.3); }}
}}

#cb-window {{
    position:fixed; bottom:100px; right:28px; z-index:99998;
    width:400px; max-width:calc(100vw - 56px);
    height:560px; max-height:calc(100vh - 140px);
    border-radius:24px; overflow:hidden;
    display:flex; flex-direction:column;
    opacity:0; transform:translateY(20px) scale(.95);
    pointer-events:none;
    transition:all .4s cubic-bezier(.34,1.56,.64,1);
    background:linear-gradient(145deg,rgba(15,23,42,.78),rgba(30,41,59,.68),rgba(51,65,85,.58),rgba(30,41,59,.72));
    backdrop-filter:blur(40px) saturate(200%) brightness(1.1);
    -webkit-backdrop-filter:blur(40px) saturate(200%) brightness(1.1);
    border:1px solid rgba(255,255,255,.15);
    box-shadow:0 24px 80px rgba(0,0,0,.4),0 0 0 .5px rgba(255,255,255,.1),
               inset 0 1px 0 rgba(255,255,255,.15),inset 0 -1px 0 rgba(255,255,255,.05);
}}
#cb-window.open {{ opacity:1; transform:translateY(0) scale(1); pointer-events:auto; }}

#cb-header {{
    padding:18px 20px; display:flex; align-items:center; gap:12px;
    border-bottom:1px solid rgba(255,255,255,.08);
    background:linear-gradient(180deg,rgba(255,255,255,.06),transparent);
    flex-shrink:0;
}}
#cb-header-icon {{
    width:38px; height:38px; border-radius:12px;
    background:linear-gradient(135deg,rgba(99,102,241,.5),rgba(139,92,246,.4));
    border:1px solid rgba(255,255,255,.15);
    display:flex; align-items:center; justify-content:center;
    font-size:18px; box-shadow:0 4px 12px rgba(99,102,241,.2);
}}
#cb-header-text h4 {{ margin:0; font-family:'Plus Jakarta Sans',sans-serif; font-size:14px; font-weight:700; color:rgba(255,255,255,.95); }}
#cb-header-text span {{ font-size:11.5px; color:rgba(255,255,255,.45); }}

#cb-messages {{
    flex:1; overflow-y:auto; padding:16px 16px 8px;
    display:flex; flex-direction:column; gap:12px;
    scrollbar-width:thin; scrollbar-color:rgba(255,255,255,.1) transparent;
}}
#cb-messages::-webkit-scrollbar {{ width:4px; }}
#cb-messages::-webkit-scrollbar-thumb {{ background:rgba(255,255,255,.1); border-radius:4px; }}

.cb-msg {{
    max-width:85%; padding:10px 14px; border-radius:16px;
    font-family:'Plus Jakarta Sans',sans-serif;
    font-size:13px; line-height:1.65; animation:cb-fadeIn .3s ease; word-wrap:break-word;
}}
@keyframes cb-fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}

.cb-msg.user {{
    align-self:flex-end;
    background:linear-gradient(135deg,rgba(99,102,241,.6),rgba(139,92,246,.5));
    color:rgba(255,255,255,.95); border-bottom-right-radius:6px;
    border:1px solid rgba(255,255,255,.1); box-shadow:0 2px 12px rgba(99,102,241,.2);
}}
.cb-msg.bot {{
    align-self:flex-start;
    background:rgba(255,255,255,.07); color:rgba(255,255,255,.88);
    border-bottom-left-radius:6px; border:1px solid rgba(255,255,255,.06);
}}
.cb-msg.bot strong {{ color:#a5b4fc; font-weight:700; }}
.cb-msg.bot em {{ color:#c4b5fd; }}
.cb-msg.bot ul,.cb-msg.bot ol {{ padding-left:18px; margin:6px 0; }}
.cb-msg.bot li {{ margin-bottom:3px; }}
.cb-msg.bot code {{ background:rgba(99,102,241,.15); padding:1px 5px; border-radius:4px; font-size:12px; color:#c4b5fd; }}
.cb-msg.bot h3,.cb-msg.bot h4 {{ color:#a5b4fc; margin:8px 0 4px; font-size:13.5px; font-weight:700; }}
.cb-msg.bot p {{ margin:4px 0; }}
.cb-msg.bot hr {{ border:none; border-top:1px solid rgba(255,255,255,.08); margin:8px 0; }}

.cb-typing {{
    display:flex; gap:4px; padding:12px 18px; align-self:flex-start;
    background:rgba(255,255,255,.07); border-radius:16px;
    border-bottom-left-radius:6px; border:1px solid rgba(255,255,255,.06);
}}
.cb-typing span {{
    width:7px; height:7px; border-radius:50%;
    background:rgba(165,180,252,.6); animation:cb-bounce 1.4s ease-in-out infinite;
}}
.cb-typing span:nth-child(2) {{ animation-delay:.15s; }}
.cb-typing span:nth-child(3) {{ animation-delay:.3s; }}
@keyframes cb-bounce {{ 0%,60%,100% {{ transform:translateY(0); opacity:.4; }} 30% {{ transform:translateY(-6px); opacity:1; }} }}

#cb-input-area {{
    padding:12px 16px 16px; border-top:1px solid rgba(255,255,255,.06);
    background:linear-gradient(0deg,rgba(255,255,255,.04),transparent);
    display:flex; gap:10px; align-items:center; flex-shrink:0;
}}
#cb-input {{
    flex:1; border:1px solid rgba(255,255,255,.1); border-radius:14px;
    padding:10px 16px; font-size:13px; font-family:'Plus Jakarta Sans',sans-serif;
    color:rgba(255,255,255,.9); background:rgba(255,255,255,.06); outline:none;
    transition:all .2s ease;
}}
#cb-input::placeholder {{ color:rgba(255,255,255,.3); }}
#cb-input:focus {{ border-color:rgba(99,102,241,.5); background:rgba(255,255,255,.08); box-shadow:0 0 0 3px rgba(99,102,241,.1); }}
#cb-send {{
    width:40px; height:40px; border-radius:12px;
    border:1px solid rgba(255,255,255,.12);
    background:linear-gradient(135deg,rgba(99,102,241,.5),rgba(139,92,246,.4));
    cursor:pointer; display:flex; align-items:center; justify-content:center;
    transition:all .2s ease; flex-shrink:0;
}}
#cb-send:hover {{ background:linear-gradient(135deg,rgba(99,102,241,.7),rgba(139,92,246,.6)); transform:scale(1.05); }}
#cb-send:active {{ transform:scale(.95); }}
#cb-send svg {{ width:18px; height:18px; fill:rgba(255,255,255,.9); }}
</style>

<button id="cb-toggle" onclick="toggleChat()" aria-label="Open AI Chat">
  <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>
</button>

<div id="cb-window">
  <div id="cb-header">
    <div id="cb-header-icon">🎓</div>
    <div id="cb-header-text">
      <h4>PGSD AI Assistant</h4>
      <span>Secure proxy • Data-only mode</span>
    </div>
  </div>
  <div id="cb-messages">
    <div class="cb-msg bot">
      Halo! 👋 Saya asisten AI untuk data <strong>Performance Indicator PGSD 2026</strong>.
      <br><br>Silakan tanyakan seputar indikator, target, realisasi, atau PI Focus.
      <br><br><em>I can also answer in English.</em>
    </div>
  </div>
  <div id="cb-input-area">
    <input id="cb-input" type="text" placeholder="Tanyakan tentang data PGSD..." autocomplete="off" />
    <button id="cb-send" onclick="sendMsg()">
      <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
    </button>
  </div>
</div>

<script>
// ── NO API KEY HERE — all calls go through Python proxy ──
const PROXY = "http://127.0.0.1:{PROXY_PORT}/api/chat";
const CTX = {data_ctx_js};

const SYS = `You are an AI assistant EXCLUSIVELY for PGSD (Pendidikan Guru Sekolah Dasar) Performance Indicator Dashboard 2026.
STRICT RULES:
1. ONLY answer about the PGSD data below. REFUSE anything else politely.
2. LANGUAGE MATCHING: Reply in the SAME language the user uses.
3. Use rich markdown: **bold**, *italic*, bullet lists, ### headings.
4. Be analytical with insights, not just raw numbers.
5. If off-topic, say: "Maaf, saya hanya menjawab tentang data Performance Indicator PGSD 2026."
DATA:
${{CTX}}`;

let hist = [], isOpen = false;

function toggleChat() {{
    isOpen = !isOpen;
    document.getElementById('cb-window').classList.toggle('open', isOpen);
    document.getElementById('cb-toggle').classList.toggle('active', isOpen);
    if (isOpen) document.getElementById('cb-input').focus();
}}

function fmtMd(t) {{
    let h = t;
    h = h.replace(/^####\\s(.+)$/gm, '<h4>$1</h4>');
    h = h.replace(/^###\\s(.+)$/gm, '<h3>$1</h3>');
    h = h.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
    h = h.replace(/(?<!\\*)\\*(?!\\*)(.+?)(?<!\\*)\\*(?!\\*)/g, '<em>$1</em>');
    h = h.replace(/`(.+?)`/g, '<code>$1</code>');
    h = h.replace(/^[\\-\\•]\\s(.+)$/gm, '<li>$1</li>');
    h = h.replace(/^\\d+\\.\\s(.+)$/gm, '<li>$1</li>');
    h = h.replace(/(<li>.*?<\\/li>\\n?)+/gs, m => '<ul>'+m+'</ul>');
    h = h.replace(/^---$/gm, '<hr>');
    h = h.replace(/\\n\\n/g, '</p><p>');
    h = h.replace(/\\n/g, '<br>');
    if (!h.startsWith('<')) h = '<p>'+h+'</p>';
    return h;
}}

function addMsg(text, role) {{
    const c = document.getElementById('cb-messages');
    const d = document.createElement('div');
    d.className = 'cb-msg '+role;
    d.innerHTML = role==='bot' ? fmtMd(text) : text.replace(/</g,'&lt;').replace(/>/g,'&gt;');
    c.appendChild(d); c.scrollTop = c.scrollHeight;
    return d;
}}

function showTyping() {{
    const c = document.getElementById('cb-messages');
    const d = document.createElement('div');
    d.className='cb-typing'; d.id='cb-typing-ind';
    d.innerHTML='<span></span><span></span><span></span>';
    c.appendChild(d); c.scrollTop=c.scrollHeight;
}}
function hideTyping() {{ const e=document.getElementById('cb-typing-ind'); if(e) e.remove(); }}

async function typewrite(el, text, speed) {{
    const full = fmtMd(text);
    el.innerHTML = '';
    const box = document.getElementById('cb-messages');
    let i=0, inTag=false;
    return new Promise(ok => {{
        const tm = setInterval(() => {{
            if (i>=full.length) {{ el.innerHTML=full; clearInterval(tm); ok(); return; }}
            if (full[i]==='<') inTag=true;
            if (inTag) {{ if (full[i]==='>') {{ inTag=false; el.innerHTML=full.substring(0,i+1); }} }}
            else {{ el.innerHTML=full.substring(0,i+1); }}
            box.scrollTop=box.scrollHeight;
            i++;
        }}, speed);
    }});
}}

async function sendMsg() {{
    const inp = document.getElementById('cb-input');
    const text = inp.value.trim();
    if (!text) return;
    inp.value=''; inp.disabled=true;
    document.getElementById('cb-send').style.pointerEvents='none';
    addMsg(text, 'user');
    hist.push({{ role:'user', content:text }});
    showTyping();
    try {{
        const msgs = [{{ role:'system', content:SYS }}, ...hist.slice(-10)];
        const resp = await fetch(PROXY, {{
            method:'POST',
            headers:{{'Content-Type':'application/json'}},
            body:JSON.stringify({{ messages:msgs }})
        }});
        hideTyping();
        if (resp.ok) {{
            const data = await resp.json();
            const reply = data.choices[0].message.content;
            hist.push({{ role:'assistant', content:reply }});
            const bd = document.createElement('div');
            bd.className='cb-msg bot';
            document.getElementById('cb-messages').appendChild(bd);
            await typewrite(bd, reply, 8);
        }} else {{
            const ed = await resp.json().catch(()=>({{}}));
            addMsg('⚠️ Error: '+(ed.error?.message||resp.statusText), 'bot');
        }}
    }} catch (err) {{
        hideTyping();
        addMsg('⚠️ Koneksi ke server gagal. Pastikan aplikasi berjalan dengan benar.', 'bot');
    }}
    inp.disabled=false;
    document.getElementById('cb-send').style.pointerEvents='auto';
    inp.focus();
}}

document.getElementById('cb-input').addEventListener('keydown', function(e) {{
    if (e.key==='Enter' && !e.shiftKey) {{ e.preventDefault(); sendMsg(); }}
}});
</script>
"""

components.html(chatbot_html, height=700, scrolling=False)
