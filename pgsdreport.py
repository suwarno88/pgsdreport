import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import json, os, requests

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="PGSD Performance Dashboard 2026", page_icon="🎓",
                   layout="wide", initial_sidebar_state="expanded")

# ── Secrets helper ───────────────────────────────────────────────────────────
def _secret(key, fb=""):
    try: return st.secrets[key]
    except Exception: return os.environ.get(key, fb)

_API_KEY  = _secret("OPENAI_API_KEY")
_API_URL  = _secret("OPENAI_ENDPOINT", "https://api.openai.com/v1/chat/completions")
_MODEL    = _secret("OPENAI_MODEL", "gpt-4.1")

# ── Light / Dark mode ────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def _is_dark():
    return st.session_state.theme == "dark"

# ── Dynamic CSS ──────────────────────────────────────────────────────────────
def _inject_css():
    if _is_dark():
        bg1, bg2, bg3 = "#0f172a", "#1e293b", "rgba(30,41,59,0.8)"
        tx1, tx2, tx3 = "#f1f5f9", "#cbd5e1", "#94a3b8"
        accent, accent2 = "rgba(99,102,241,0.15)", "rgba(99,102,241,0.3)"
        hero = "linear-gradient(135deg,#312e81 0%,#4f46e5 40%,#7c3aed 100%)"
        card_border = "rgba(99,102,241,0.15)"
        sidebar_bg = "linear-gradient(180deg,#1e293b 0%,#0f172a 100%)"
        tab_bg, tab_sel = "rgba(30,41,59,0.6)", "rgba(79,70,229,0.2)"
    else:
        bg1, bg2, bg3 = "#f8fafc", "#ffffff", "rgba(255,255,255,0.95)"
        tx1, tx2, tx3 = "#0f172a", "#334155", "#64748b"
        accent, accent2 = "rgba(99,102,241,0.08)", "rgba(99,102,241,0.15)"
        hero = "linear-gradient(135deg,#6366f1 0%,#818cf8 40%,#a78bfa 100%)"
        card_border = "rgba(99,102,241,0.12)"
        sidebar_bg = "linear-gradient(180deg,#f1f5f9 0%,#e2e8f0 100%)"
        tab_bg, tab_sel = "rgba(241,245,249,0.8)", "rgba(99,102,241,0.1)"

    st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
html,body,[class*="css"] {{ font-family:'Plus Jakarta Sans',sans-serif; }}
#MainMenu {{visibility:hidden;}} footer {{visibility:hidden;}} header {{visibility:hidden;}}
.stApp {{ background:{bg1}; }}
section[data-testid="stSidebar"] {{ background:{sidebar_bg}; border-right:1px solid {card_border}; }}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] label {{ color:{tx2}!important; }}

.hero-banner {{ background:{hero}; border-radius:16px; padding:2rem 2.5rem; margin-bottom:1.5rem;
    position:relative; overflow:hidden; box-shadow:0 20px 60px rgba(79,70,229,0.25); }}
.hero-banner::before {{ content:''; position:absolute; top:-50%; right:-20%; width:400px; height:400px;
    background:radial-gradient(circle,rgba(255,255,255,0.08) 0%,transparent 70%); border-radius:50%; }}
.hero-banner h1 {{ color:#fff; font-size:1.9rem; font-weight:800; margin:0 0 .3rem 0; }}
.hero-banner p {{ color:rgba(255,255,255,.8); font-size:1rem; margin:0; }}

.kpi-card {{ background:{bg3}; backdrop-filter:blur(10px); border:1px solid {card_border};
    border-radius:14px; padding:1.4rem 1.6rem; text-align:center; transition:all .3s ease;
    box-shadow:0 4px 20px rgba(0,0,0,{'0.15' if _is_dark() else '0.04'}); }}
.kpi-card:hover {{ border-color:rgba(99,102,241,0.5); transform:translateY(-2px); }}
.kpi-label {{ color:{tx3}; font-size:.78rem; font-weight:600; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:.6rem; }}
.kpi-value {{ color:{tx1}; font-size:2.2rem; font-weight:800; line-height:1; margin-bottom:.3rem; }}
.kpi-sub {{ font-size:.8rem; font-weight:500; color:{tx3}; }}
.kpi-green {{color:#10b981;}} .kpi-yellow {{color:#f59e0b;}} .kpi-red {{color:#ef4444;}} .kpi-blue {{color:#3b82f6;}}

.section-header {{ color:{tx1}; font-size:1.25rem; font-weight:700; margin:1.8rem 0 1rem 0;
    padding-bottom:.5rem; border-bottom:2px solid {accent2}; display:flex; align-items:center; gap:.5rem; }}

div[data-testid="stMetric"] {{ background:{bg3}; border:1px solid {card_border}; border-radius:14px; padding:1rem 1.2rem; }}
.stTabs [data-baseweb="tab-list"] {{ gap:8px; background:transparent; }}
.stTabs [data-baseweb="tab"] {{ background:{tab_bg}; border-radius:10px 10px 0 0;
    border:1px solid {card_border}; color:{tx3}; font-weight:600; padding:.6rem 1.2rem; }}
.stTabs [aria-selected="true"] {{ background:{tab_sel}!important;
    border-color:rgba(99,102,241,.4)!important; color:#6366f1!important; }}
div[data-testid="stExpander"] {{ background:{bg3}; border:1px solid {card_border}; border-radius:12px; }}
.stSelectbox label,.stMultiSelect label,.stRadio label {{ color:{tx2}!important; font-weight:600!important; }}

.info-box {{ background:{bg3}; border:1px solid {card_border}; border-radius:14px;
    padding:1.5rem 2rem; color:{tx1}; font-size:.92rem; line-height:1.7; }}
.info-box h3 {{ color:#6366f1; margin-top:1rem; margin-bottom:.4rem; font-size:1rem; }}
.info-box strong {{ color:#6366f1; }}
.info-box ul {{ padding-left:1.2rem; }} .info-box li {{ margin-bottom:.4rem; }}

.strat-card {{ background:{bg3}; border:1px solid {card_border}; border-left:4px solid #6366f1;
    border-radius:0 12px 12px 0; padding:1rem 1.4rem; margin-bottom:.7rem; }}
.strat-num {{ display:inline-flex; align-items:center; justify-content:center; width:28px; height:28px;
    border-radius:8px; background:rgba(99,102,241,0.12); color:#6366f1; font-weight:700;
    font-size:.82rem; margin-right:.6rem; flex-shrink:0; }}
.strat-title {{ color:{tx1}; font-weight:700; font-size:.92rem; }}
.strat-desc {{ color:{tx2}; font-size:.85rem; margin-top:.3rem; }}
</style>""", unsafe_allow_html=True)

_inject_css()

# ── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    fp = os.path.join(os.path.dirname(__file__),
                      "ReportRealization_Pendidikan_Guru_Sekolah_Dasar__PGSD_.xlsx")
    df = pd.read_excel(fp, header=0)
    df.columns = ["No","Year","Performance Indicator","Unit Name",
                   "Target Q1","Target Q2","Target Q3","Target Q4",
                   "Realization","Score","PI Focus"]
    def _parse(val):
        if pd.isna(val): return np.nan
        s = str(val).strip()
        if any(c.isalpha() for c in s.replace("NaN","")): return np.nan
        try: return float(s.replace(".","").replace(",","."))
        except: return np.nan
    for c in ["Target Q1","Target Q2","Target Q3","Target Q4","Realization","Score"]:
        df[c] = df[c].apply(_parse)
    df["No"] = pd.to_numeric(df["No"], errors="coerce").astype("Int64")
    df["PI Focus"] = df["PI Focus"].fillna("NO").astype(str).str.strip().str.upper()
    return df

@st.cache_data
def load_kegiatan():
    fp = os.path.join(os.path.dirname(__file__), "Kegiatan_yang_telah_terlaksana.xlsx")
    df = pd.read_excel(fp, header=0)
    df.columns = ["No","Kegiatan","PI/KPI Terkait","Waktu","Notes"]
    df = df.dropna(how="all")
    for c in df.columns:
        df[c] = df[c].astype(str).str.replace("\u200b","").str.strip()
        df[c] = df[c].replace({"nan":"","NaN":"","None":""})
    return df

df = load_data()
kg = load_kegiatan()

# ── Data context for AI ──────────────────────────────────────────────────────
@st.cache_data
def build_ctx(_df):
    L = ["=== DATA PI PGSD 2026 ===",
         f"Total: {len(_df)} | PI Focus: {len(_df[_df['PI Focus']=='YES'])}\n"]
    for _,r in _df.iterrows():
        no = int(r['No']) if pd.notna(r['No']) else '?'
        qs = ", ".join(f"Q{i+1}:{r[f'Target Q{i+1}']:,.0f}" if pd.notna(r[f'Target Q{i+1}']) else f"Q{i+1}:-" for i in range(4))
        rl = f"{r['Realization']:,.0f}" if pd.notna(r['Realization']) else "-"
        L.append(f"#{no}. {r['Performance Indicator']} | {qs} | Real:{rl} | Focus:{r['PI Focus']}")
    return "\n".join(L)

data_ctx = build_ctx(df)

# ── Helpers ──────────────────────────────────────────────────────────────────
_chart_text = "#cbd5e1" if _is_dark() else "#1e293b"
_chart_tick = "#94a3b8" if _is_dark() else "#475569"

PL = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans,sans-serif", color=_chart_text),
    margin=dict(l=40,r=30,t=50,b=40),
    legend=dict(bgcolor="rgba(30,41,59,0.6)" if _is_dark() else "rgba(255,255,255,0.9)",
                bordercolor="rgba(99,102,241,0.2)", borderwidth=1,
                font=dict(size=11, color=_chart_text)),
    xaxis=dict(gridcolor="rgba(99,102,241,0.08)" if _is_dark() else "rgba(99,102,241,0.12)",
               zerolinecolor="rgba(99,102,241,0.15)",
               tickfont=dict(color=_chart_tick),
               title_font=dict(color=_chart_text)),
    yaxis=dict(gridcolor="rgba(99,102,241,0.08)" if _is_dark() else "rgba(99,102,241,0.12)",
               zerolinecolor="rgba(99,102,241,0.15)",
               tickfont=dict(color=_chart_tick),
               title_font=dict(color=_chart_text)))
C = {"pri":"#6366f1","sec":"#a78bfa","acc":"#22d3ee",
     "ok":"#10b981","warn":"#f59e0b","bad":"#ef4444","real":"#22d3ee"}

def pct(r,t):
    if pd.isna(r) or pd.isna(t) or t==0: return None
    return r/t*100
def acol(p):
    if p is None: return "#64748b"
    return C["ok"] if p>=100 else (C["warn"] if p>=75 else C["bad"])
def alab(p):
    if p is None: return "N/A"
    return "✅ Achieved" if p>=100 else ("⚠️ On Track" if p>=75 else "❌ Below Target")

def call_ai(sys, usr, mt=3000):
    r = requests.post(_API_URL,
        headers={"Content-Type":"application/json","Authorization":f"Bearer {_API_KEY}"},
        json={"model":_MODEL,"messages":[{"role":"system","content":sys},
              {"role":"user","content":usr}],"max_tokens":mt,"temperature":0.7}, timeout=90)
    if r.status_code==200: return r.json()["choices"][0]["message"]["content"]
    raise RuntimeError(f"API {r.status_code}: {r.text[:200]}")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div style="text-align:center;padding:1rem 0 1rem 0;">
        <div style="font-size:2.5rem;margin-bottom:.3rem;">🎓</div>
        <div style="color:#6366f1;font-weight:800;font-size:1.15rem;">PGSD Dashboard</div>
        <div style="color:#94a3b8;font-size:.75rem;">Performance Indicator 2026</div>
    </div>""", unsafe_allow_html=True)

    # Theme toggle
    theme_label = "🌙 Dark Mode" if _is_dark() else "☀️ Light Mode"
    if st.button(theme_label, use_container_width=True):
        st.session_state.theme = "light" if _is_dark() else "dark"
        st.rerun()

    st.markdown("---")
    selected_quarter = st.selectbox("📅 Pilih Kuartal", ["Q1","Q2","Q3","Q4"], index=3)
    qcol = f"Target {selected_quarter}"
    focus_filter = st.radio("🎯 Filter PI Focus", ["Semua","YES (Fokus)","NO"], index=0)
    cats = {
        "Semua Kategori": None,
        "🎓 Students": ["Student","Intake","Active","NR Students","Graduation"],
        "💰 Revenue": ["Revenue","revenue"],
        "🤝 Partnership": ["Partnership","partner"],
        "📚 Research": ["SCOPUS","Citation","Research","publication","paper","IP(s)","MULTIDIS"],
        "🌐 International": ["International","Inbound","Outbound"],
        "👩‍🏫 Employment": ["Employment","Entrepreneur","Employability"],
        "📊 Others": None,
    }
    sel_cat = st.selectbox("📂 Kategori", list(cats.keys()), index=0)
    st.markdown("---")
    st.markdown(f"""<div style="padding:.8rem;background:rgba(99,102,241,.08);border-radius:10px;
        border:1px solid rgba(99,102,241,.15);">
        <div style="color:#6366f1;font-weight:700;font-size:.82rem;margin-bottom:.5rem;">ℹ️ Petunjuk</div>
        <div style="color:{'#94a3b8' if _is_dark() else '#64748b'};font-size:.74rem;line-height:1.5;">
            • Pilih kuartal untuk perbandingan target vs realisasi<br>
            • Tab "💬 AI Chat" untuk chatbot interaktif<br>
            • Tab "🤖 AI Summary" untuk ringkasan otomatis<br>
            • Gunakan tombol tema untuk light/dark mode
        </div></div>""", unsafe_allow_html=True)

# ── Filters ──────────────────────────────────────────────────────────────────
fdf = df.copy()
if focus_filter=="YES (Fokus)": fdf = fdf[fdf["PI Focus"]=="YES"]
elif focus_filter=="NO": fdf = fdf[fdf["PI Focus"]=="NO"]
if sel_cat not in ("Semua Kategori","📊 Others"):
    kw = cats[sel_cat]
    if kw: fdf = fdf[fdf["Performance Indicator"].str.contains("|".join(kw), case=False, na=False)]
elif sel_cat=="📊 Others":
    akw = [w for v in cats.values() if v for w in v]
    fdf = fdf[~fdf["Performance Indicator"].str.contains("|".join(akw), case=False, na=False)]

# ── Hero Banner ──────────────────────────────────────────────────────────────
st.markdown(f"""<div class="hero-banner">
    <h1>📊 Performance Indicator Dashboard</h1>
    <p>Jurusan Pendidikan Guru Sekolah Dasar (PGSD) — 2026 &nbsp;|&nbsp;
    Kuartal: <strong>{selected_quarter}</strong> &nbsp;|&nbsp;
    <strong>{len(fdf)}</strong>/{len(df)} indikator</p>
</div>""", unsafe_allow_html=True)

# ── KPI Cards ────────────────────────────────────────────────────────────────
comp = fdf.dropna(subset=[qcol,"Realization"]).copy()
comp["A%"] = comp.apply(lambda r: pct(r["Realization"], r[qcol]), axis=1)
vc = comp.dropna(subset=["A%"])
t_ind = len(fdf); n_m = len(vc)
n_ach = len(vc[vc["A%"]>=100]) if len(vc)>0 else 0
avg_a = vc["A%"].mean() if len(vc)>0 else 0
n_pf = len(fdf[fdf["PI Focus"]=="YES"])
acls = "kpi-green" if avg_a>=100 else ("kpi-yellow" if avg_a>=75 else "kpi-red")

c1,c2,c3,c4,c5 = st.columns(5)
with c1: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Indikator</div><div class="kpi-value kpi-blue">{t_ind}</div><div class="kpi-sub">ditampilkan</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Terukur ({selected_quarter})</div><div class="kpi-value" style="color:#a78bfa;">{n_m}</div><div class="kpi-sub">target & realisasi</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Tercapai</div><div class="kpi-value kpi-green">{n_ach}</div><div class="kpi-sub">≥ 100%</div></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Rata-rata</div><div class="kpi-value {acls}">{avg_a:.1f}%</div><div class="kpi-sub">capaian {selected_quarter}</div></div>', unsafe_allow_html=True)
with c5: st.markdown(f'<div class="kpi-card"><div class="kpi-label">PI Focus</div><div class="kpi-value" style="color:#f59e0b;">{n_pf}</div><div class="kpi-sub">prioritas tinggi</div></div>', unsafe_allow_html=True)
st.markdown("<div style='height:.8rem;'></div>", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8 = st.tabs([
    "📊 Target vs Realisasi","📈 Analisis Kuartal","🎯 PI Focus","📋 Data Lengkap",
    "📝 Kegiatan","📣 Rencana Strategis","🤖 AI Summary","💬 AI Chat"])

# ━━ TAB 1: Target vs Realisasi (show ALL indicators) ━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    # Use ALL filtered indicators, fill missing target/realization with 0
    t1df = fdf.copy()
    t1df["Tgt_display"] = t1df[qcol].fillna(0)
    t1df["Real_display"] = t1df["Realization"].fillna(0)
    if len(t1df)==0:
        st.warning(f"Tidak ada data untuk ditampilkan.")
    else:
        t1df["SN"] = t1df["Performance Indicator"].apply(lambda x: (x[:55]+"…") if len(str(x))>55 else x)
        t1df["A%"] = t1df.apply(lambda r: pct(r["Realization"], r[qcol]), axis=1)

        # ── 1) Achievement chart FIRST (only rows with actual realization & target) ──
        ach_df = t1df[t1df["A%"].notna()].sort_values("A%", ascending=True)
        if len(ach_df) > 0:
            st.markdown(f'<div class="section-header">🏆 Persentase Capaian ({selected_quarter})</div>', unsafe_allow_html=True)
            fig_ach = go.Figure(go.Bar(y=ach_df["SN"], x=ach_df["A%"], orientation="h",
                marker=dict(color=[acol(v) for v in ach_df["A%"]]),
                text=ach_df["A%"].apply(lambda v:f"{v:.1f}%"), textposition="outside",
                textfont=dict(size=10, color=_chart_text)))
            fig_ach.add_vline(x=100, line_dash="dash", line_color="#f59e0b", line_width=1.5,
                annotation_text="100%", annotation_font=dict(color="#f59e0b", size=10))
            fig_ach.update_layout(PL, height=max(400, len(ach_df)*45),
                title=dict(text="Achievement Rate (%)", font=dict(size=16, color=_chart_text)),
                xaxis=dict(title="Achievement %", range=[0, max(ach_df["A%"].max()*1.2, 120)]),
                yaxis=dict(tickfont=dict(size=10, color=_chart_tick)), showlegend=False)
            st.plotly_chart(fig_ach, use_container_width=True)

        # ── 2) Target vs Realisasi SECOND (ALL indicators — including those without data) ──
        st.markdown(f'<div class="section-header">📊 Target {selected_quarter} vs Realisasi (Semua Indikator)</div>', unsafe_allow_html=True)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(y=t1df["SN"], x=t1df["Tgt_display"],
            name=f"Target {selected_quarter}", orientation="h",
            marker=dict(color=C["pri"]), opacity=0.85,
            text=t1df.apply(lambda r: f"{r['Tgt_display']:,.0f}" if r["Tgt_display"]>0 else "—", axis=1),
            textposition="auto", textfont=dict(size=10)))
        fig_bar.add_trace(go.Bar(y=t1df["SN"], x=t1df["Real_display"],
            name="Realisasi", orientation="h",
            marker=dict(color=C["real"]), opacity=0.85,
            text=t1df.apply(lambda r: f"{r['Real_display']:,.0f}" if r["Real_display"]>0 else "—", axis=1),
            textposition="auto", textfont=dict(size=10)))
        fig_bar.update_layout(PL, barmode="group", height=max(600, len(t1df)*40),
            title=dict(text=f"Target {selected_quarter} vs Realisasi", font=dict(size=16, color=_chart_text)),
            yaxis=dict(autorange="reversed", tickfont=dict(size=10, color=_chart_tick)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_bar, use_container_width=True)

# ━━ TAB 2: Quarterly Analysis ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    st.markdown('<div class="section-header">📈 Tren Target per Kuartal</div>', unsafe_allow_html=True)
    opts = fdf["Performance Indicator"].tolist()
    sel = st.multiselect("Pilih indikator:", opts, default=opts[:5] if len(opts)>=5 else opts)
    if sel:
        sdf = fdf[fdf["Performance Indicator"].isin(sel)].copy()
        qcs = [c for c in ["Target Q1","Target Q2","Target Q3","Target Q4"] if sdf[c].notna().any()]
        if qcs:
            m = sdf.melt(id_vars=["No","Performance Indicator","Realization"], value_vars=qcs,
                         var_name="Q", value_name="TV").dropna(subset=["TV"])
            m["QL"] = m["Q"].str.replace("Target ","")
            m["SN"] = m["Performance Indicator"].apply(lambda x:(x[:50]+"…") if len(str(x))>50 else x)
            fig = px.line(m, x="QL", y="TV", color="SN", markers=True,
                          color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_traces(line=dict(width=2.5), marker=dict(size=8))
            fig.update_layout(PL, height=500, title=dict(text="Tren Target Q1→Q4", font=dict(size=16)),
                xaxis_title="Kuartal", yaxis_title="Nilai Target",
                legend=dict(orientation="h", yanchor="top", y=-0.15, font=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True)

            st.markdown('<div class="section-header">🕸️ Radar: Target Q4 vs Realisasi</div>', unsafe_allow_html=True)
            rdf = sdf.dropna(subset=["Target Q4","Realization"]).copy()
            if len(rdf)>=3:
                rdf["SN"] = rdf["Performance Indicator"].apply(lambda x:(x[:35]+"…") if len(str(x))>35 else x)
                mx = rdf[["Target Q4","Realization"]].max().max()
                if mx>0:
                    rdf["Tn"]=rdf["Target Q4"]/mx*100; rdf["Rn"]=rdf["Realization"]/mx*100
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(r=rdf["Tn"].tolist()+[rdf["Tn"].iloc[0]],
                        theta=rdf["SN"].tolist()+[rdf["SN"].iloc[0]], fill="toself", name="Target Q4",
                        line=dict(color=C["pri"],width=2), fillcolor="rgba(99,102,241,0.15)"))
                    fig.add_trace(go.Scatterpolar(r=rdf["Rn"].tolist()+[rdf["Rn"].iloc[0]],
                        theta=rdf["SN"].tolist()+[rdf["SN"].iloc[0]], fill="toself", name="Realisasi",
                        line=dict(color=C["real"],width=2), fillcolor="rgba(34,211,238,0.12)"))
                    fig.update_layout(PL, height=500,
                        polar=dict(bgcolor="rgba(0,0,0,0)",
                            radialaxis=dict(visible=True, gridcolor="rgba(99,102,241,0.1)"),
                            angularaxis=dict(gridcolor="rgba(99,102,241,0.1)", tickfont=dict(size=9))),
                        title=dict(text="Radar Comparison (Normalized)", font=dict(size=16)))
                    st.plotly_chart(fig, use_container_width=True)
            else: st.info("Pilih minimal 3 indikator dengan Target Q4 dan Realisasi.")
        else: st.info("Tidak ada target kuartal numerik.")
    else: st.info("Pilih minimal satu indikator.")

    st.markdown('<div class="section-header">📊 Distribusi Skor</div>', unsafe_allow_html=True)
    scdf = fdf.dropna(subset=["Score"])
    if len(scdf)>0:
        fig = px.histogram(scdf, x="Score", nbins=10, color_discrete_sequence=[C["sec"]])
        fig.update_layout(PL, height=350, title=dict(text="Distribusi Skor", font=dict(size=15)), bargap=0.1)
        fig.update_traces(marker_line_width=0, opacity=0.85)
        st.plotly_chart(fig, use_container_width=True)

# ━━ TAB 3: PI Focus ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    st.markdown('<div class="section-header">🎯 Indikator PI Focus</div>', unsafe_allow_html=True)
    pf = df[df["PI Focus"]=="YES"].copy()
    if len(pf)==0: st.info("Tidak ada indikator PI Focus.")
    else:
        for _,row in pf.iterrows():
            tv=row[qcol]; rv=row["Realization"]; p=pct(rv,tv); co=acol(p); lb=alab(p)
            pt=f"{p:.1f}%" if p else "N/A"
            tt=f"{tv:,.2f}" if pd.notna(tv) else "—"
            rt=f"{rv:,.2f}" if pd.notna(rv) else "—"
            sc=f"{row['Score']:,.2f}" if pd.notna(row['Score']) else "—"
            st.markdown(f"""<div style="background:{'rgba(30,41,59,.7)' if _is_dark() else 'rgba(255,255,255,.9)'};
                border:1px solid rgba(99,102,241,.15); border-left:4px solid {co}; border-radius:12px;
                padding:1.2rem 1.5rem; margin-bottom:.8rem;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:.8rem;">
                    <div style="flex:1;min-width:250px;">
                        <div style="color:{'#e2e8f0' if _is_dark() else '#0f172a'};font-weight:700;font-size:.95rem;margin-bottom:.4rem;">
                            #{int(row['No'])} — {row['Performance Indicator']}</div>
                        <div style="color:#94a3b8;font-size:.78rem;">Skor: {sc}</div>
                    </div>
                    <div style="display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap;">
                        <div style="text-align:center;"><div style="color:#94a3b8;font-size:.7rem;text-transform:uppercase;">Target {selected_quarter}</div><div style="color:#6366f1;font-size:1.1rem;font-weight:700;">{tt}</div></div>
                        <div style="text-align:center;"><div style="color:#94a3b8;font-size:.7rem;text-transform:uppercase;">Realisasi</div><div style="color:#22d3ee;font-size:1.1rem;font-weight:700;">{rt}</div></div>
                        <div style="text-align:center;"><div style="color:#94a3b8;font-size:.7rem;text-transform:uppercase;">Capaian</div><div style="color:{co};font-size:1.1rem;font-weight:700;">{pt}</div></div>
                        <div style="font-size:.82rem;">{lb}</div>
                    </div></div></div>""", unsafe_allow_html=True)

        fc=pf.copy(); fc["Ach"]=fc.apply(lambda r:pct(r["Realization"],r[qcol]),axis=1)
        fv=fc.dropna(subset=["Ach"])
        if len(fv)>0:
            a=len(fv[fv["Ach"]>=100]); na_=len(fv)-a; nd=len(fc)-len(fv)
            fig=go.Figure(go.Pie(labels=["Tercapai ≥100%","Belum Tercapai","Belum Tersedia"],
                values=[a,na_,nd],hole=0.6,
                marker=dict(colors=[C["ok"],C["bad"],"#475569"],line=dict(width=2,color="#1e293b" if _is_dark() else "#fff")),
                textinfo="label+value",textfont=dict(size=12)))
            fig.update_layout(PL, height=400,
                title=dict(text=f"Status PI Focus — {selected_quarter}", font=dict(size=16)),
                annotations=[dict(text=f"{a}/{len(fc)}",x=0.5,y=0.5,
                    font=dict(size=28,color=PL["font"]["color"],family="Plus Jakarta Sans"),showarrow=False)])
            st.plotly_chart(fig, use_container_width=True)


# ━━ TAB 4: Data Lengkap ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab4:
    st.markdown('<div class="section-header">📋 Tabel Data Lengkap</div>', unsafe_allow_html=True)
    ddf=fdf.copy()
    ddf["Achievement %"]=ddf.apply(lambda r:pct(r["Realization"],r[qcol]),axis=1)
    ddf["Status"]=ddf["Achievement %"].apply(alab)
    search=st.text_input("🔍 Cari indikator...", placeholder="Ketik kata kunci...", key="s4")
    if search: ddf=ddf[ddf["Performance Indicator"].str.contains(search, case=False, na=False)]
    st.markdown(f"Menampilkan **{len(ddf)}** indikator")
    cols=["No","Performance Indicator","Target Q1","Target Q2","Target Q3","Target Q4","Realization","Score","PI Focus","Achievement %","Status"]
    styler = ddf[cols].style.format({
        "Target Q1":lambda v:f"{v:,.2f}" if pd.notna(v) else "—",
        "Target Q2":lambda v:f"{v:,.2f}" if pd.notna(v) else "—",
        "Target Q3":lambda v:f"{v:,.2f}" if pd.notna(v) else "—",
        "Target Q4":lambda v:f"{v:,.2f}" if pd.notna(v) else "—",
        "Realization":lambda v:f"{v:,.2f}" if pd.notna(v) else "—",
        "Score":lambda v:f"{v:,.2f}" if pd.notna(v) else "—",
        "Achievement %":lambda v:f"{v:.1f}%" if pd.notna(v) else "—",})
    _sc = lambda v:"color:#10b981" if v=="✅ Achieved" else ("color:#f59e0b" if v=="⚠️ On Track" else ("color:#ef4444" if v=="❌ Below Target" else ""))
    try: styler = styler.map(_sc, subset=["Status"])
    except AttributeError: styler = styler.applymap(_sc, subset=["Status"])
    st.dataframe(styler, use_container_width=True, height=600)
    st.download_button("⬇️ Download CSV", fdf.to_csv(index=False).encode("utf-8"),
                       "pgsd_performance_2026.csv","text/csv")


# ━━ TAB 5: Kegiatan Terlaksana ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab5:
    st.markdown('<div class="section-header">📝 Kegiatan yang Telah Terlaksana</div>', unsafe_allow_html=True)
    kdf = kg.copy()
    ks = st.text_input("🔍 Cari kegiatan...", placeholder="Ketik kata kunci...", key="s5")
    if ks:
        mask = kdf.apply(lambda r: r.astype(str).str.contains(ks, case=False).any(), axis=1)
        kdf = kdf[mask]
    st.markdown(f"Menampilkan **{len(kdf)}** kegiatan")
    st.dataframe(kdf, use_container_width=True, height=550, hide_index=True)


# ━━ TAB 6: Rencana Strategis Marketing ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab6:
    st.markdown('<div class="section-header">📣 Rencana Strategis Marketing PGSD</div>', unsafe_allow_html=True)
    st.markdown(f"""<div class="info-box" style="margin-bottom:1.2rem;">
        Untuk mendukung penguatan branding dan perluasan jejaring, Program Studi PGSD
        akan melaksanakan inisiatif strategis berikut:
    </div>""", unsafe_allow_html=True)

    strats = [
        ("Pemasaran di Wilayah Surabaya (April)",
         "Melakukan kegiatan pemasaran dengan menyesuaikan jadwal tim marketing universitas."),
        ("Audiensi Kemitraan Industri",
         "Menjalin komunikasi dengan Djarum, Astra, dan Tzu Chi untuk mengeksplorasi skema beasiswa parsial bersumber dari mitra industri."),
        ("Koordinasi Kelembagaan",
         "Berkoordinasi dengan Indonesia Mengajar dalam rangka menjajaki potensi kerja sama dengan Pemerintah Daerah."),
        ("Revitalisasi Media Digital",
         "Mengoptimalkan website dan media sosial (Instagram, TikTok) melalui strategi konten storytelling yang lebih interaktif dan informatif."),
        ("Penguatan Konten Audio Visual",
         "Memproduksi video podcast bertema Pendidikan secara rutin setiap bulan."),
    ]
    for i, (title, desc) in enumerate(strats, 1):
        st.markdown(f"""<div class="strat-card">
            <div style="display:flex;align-items:flex-start;">
                <span class="strat-num">{i}</span>
                <div>
                    <div class="strat-title">{title}</div>
                    <div class="strat-desc">{desc}</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

# ━━ TAB 7: AI Summary ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab7:
    st.markdown('<div class="section-header">🤖 AI-Generated Summary</div>', unsafe_allow_html=True)
    st.caption("Klik tombol untuk ringkasan analitis otomatis menggunakan AI.")
    sl = st.selectbox("🌐 Bahasa", ["Bahasa Indonesia","English"], index=0, key="slang")
    _,bc,_ = st.columns([1,1,1])
    with bc:
        gen = st.button("✨ Generate Summary", type="primary", use_container_width=True)
    if gen:
        with st.spinner("🔄 AI sedang menganalisis..."):
            lang = "Jawab dalam Bahasa Indonesia." if sl=="Bahasa Indonesia" else "Answer in English."
            sp = f"""Anda adalah analis data Performance Indicator PGSD 2026. {lang}
Buat ringkasan analitis komprehensif:
1. **Overview** 2. **Indikator Tercapai** 3. **Perlu Perhatian** 4. **PI Focus** 5. **Rekomendasi**
Gunakan markdown (heading, bold, bullet)."""
            try:
                st.markdown(call_ai(sp, data_ctx))
            except Exception as e:
                st.error(f"Error: {e}")


# ━━ TAB 8: AI Chat (Native Streamlit — reads data directly, no server) ━━━━━
with tab8:
    st.markdown('<div class="section-header">💬 AI Chatbot — PGSD Data Assistant</div>', unsafe_allow_html=True)
    st.caption("Tanyakan apa saja seputar data Performance Indicator PGSD 2026. Chatbot membaca langsung dari data aplikasi.")

    SYS_CHAT = f"""Anda adalah asisten AI KHUSUS untuk data Performance Indicator PGSD 2026.
ATURAN KETAT:
1. HANYA jawab pertanyaan tentang data PGSD di bawah. TOLAK pertanyaan lain dengan sopan.
2. BAHASA: Jawab dalam bahasa yang SAMA dengan pengguna. Indonesia → Indonesia. English → English.
3. Gunakan format rich: **bold**, *italic*, bullet list, heading.
4. Berikan analisis dan insight, bukan hanya angka mentah.
5. Jika di luar topik: "Maaf, saya hanya menjawab tentang data PI PGSD 2026."

DATA:
{data_ctx}"""

    if "chat_msgs" not in st.session_state:
        st.session_state.chat_msgs = [
            {"role":"assistant","content":"Halo! 👋 Saya asisten AI untuk data **Performance Indicator PGSD 2026**.\n\nSilakan tanyakan seputar indikator, target kuartal, realisasi, skor, atau PI Focus.\n\n*I can also answer in English if you ask in English.*"}
        ]

    # Display chat history
    for msg in st.session_state.chat_msgs:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Tanyakan tentang data PGSD..."):
        st.session_state.chat_msgs.append({"role":"user","content":prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Berpikir..."):
                reply = ""
                try:
                    api_msgs = [{"role":"system","content":SYS_CHAT}]
                    for m in st.session_state.chat_msgs[-10:]:
                        api_msgs.append({"role":m["role"],"content":m["content"]})
                    resp = requests.post(_API_URL,
                        headers={"Content-Type":"application/json","Authorization":f"Bearer {_API_KEY}"},
                        json={"model":_MODEL,"messages":api_msgs,"max_tokens":1500,"temperature":0.7},
                        timeout=90)
                    if resp.status_code == 200:
                        reply = resp.json()["choices"][0]["message"]["content"]
                    else:
                        reply = f"⚠️ Error {resp.status_code}: {resp.json().get('error',{}).get('message','Unknown error')}"
                except Exception as e:
                    reply = f"⚠️ Error: {str(e)}"
                st.markdown(reply)
        st.session_state.chat_msgs.append({"role":"assistant","content":reply})

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""<div style="text-align:center;padding:1rem 0 .5rem 0;">
    <div style="color:{'#475569' if _is_dark() else '#94a3b8'};font-size:.78rem;font-weight:500;">
        🎓 PGSD Performance Dashboard 2026 &nbsp;|&nbsp; Streamlit & Plotly &nbsp;|&nbsp; Powered by OpenAI
    </div></div>""", unsafe_allow_html=True)
