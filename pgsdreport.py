import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os

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

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Hide default Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Main background */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    border-right: 1px solid rgba(99, 102, 241, 0.2);
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] label {
    color: #cbd5e1 !important;
}

/* Hero banner */
.hero-banner {
    background: linear-gradient(135deg, #312e81 0%, #4f46e5 40%, #7c3aed 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(79, 70, 229, 0.3);
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-banner h1 {
    color: #ffffff;
    font-size: 1.9rem;
    font-weight: 800;
    margin: 0 0 0.3rem 0;
    letter-spacing: -0.5px;
}
.hero-banner p {
    color: rgba(255,255,255,0.8);
    font-size: 1rem;
    margin: 0;
    font-weight: 400;
}

/* KPI Cards */
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
.kpi-card:hover {
    border-color: rgba(99, 102, 241, 0.5);
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(99, 102, 241, 0.15);
}
.kpi-label {
    color: #94a3b8;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 0.6rem;
}
.kpi-value {
    color: #f1f5f9;
    font-size: 2.2rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 0.3rem;
}
.kpi-sub {
    font-size: 0.8rem;
    font-weight: 500;
}
.kpi-green { color: #34d399; }
.kpi-yellow { color: #fbbf24; }
.kpi-red { color: #f87171; }
.kpi-blue { color: #60a5fa; }

/* Section headers */
.section-header {
    color: #e2e8f0;
    font-size: 1.25rem;
    font-weight: 700;
    margin: 1.8rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid rgba(99, 102, 241, 0.3);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Chart containers */
.chart-container {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(99, 102, 241, 0.1);
    border-radius: 14px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
}

/* Table styling */
.dataframe-container {
    background: rgba(30, 41, 59, 0.6);
    border-radius: 14px;
    padding: 1rem;
    border: 1px solid rgba(99, 102, 241, 0.1);
}

/* Badge styles */
.badge {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.badge-yes {
    background: rgba(52, 211, 153, 0.15);
    color: #34d399;
    border: 1px solid rgba(52, 211, 153, 0.3);
}
.badge-no {
    background: rgba(148, 163, 184, 0.1);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.2);
}

/* Status pills */
.status-achieved {
    background: rgba(52, 211, 153, 0.15);
    color: #34d399;
    padding: 0.25rem 0.8rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
}
.status-below {
    background: rgba(248, 113, 113, 0.15);
    color: #f87171;
    padding: 0.25rem 0.8rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
}
.status-na {
    background: rgba(148, 163, 184, 0.1);
    color: #64748b;
    padding: 0.25rem 0.8rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
}

/* Streamlit overrides */
div[data-testid="stMetric"] {
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 14px;
    padding: 1rem 1.2rem;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    background: rgba(30, 41, 59, 0.6);
    border-radius: 10px 10px 0 0;
    border: 1px solid rgba(99, 102, 241, 0.15);
    color: #94a3b8;
    font-weight: 600;
    padding: 0.6rem 1.2rem;
}
.stTabs [aria-selected="true"] {
    background: rgba(79, 70, 229, 0.2) !important;
    border-color: rgba(99, 102, 241, 0.4) !important;
    color: #a5b4fc !important;
}
div[data-testid="stExpander"] {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(99, 102, 241, 0.1);
    border-radius: 12px;
}
.stSelectbox label, .stMultiSelect label, .stRadio label {
    color: #cbd5e1 !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    file_path = os.path.join(os.path.dirname(__file__), "data",
                             "ReportRealization_Pendidikan_Guru_Sekolah_Dasar__PGSD_.xlsx")
    df = pd.read_excel(file_path, header=0)
    df.columns = ["No", "Year", "Performance Indicator", "Unit Name",
                   "Target Q1", "Target Q2", "Target Q3", "Target Q4",
                   "Realization", "Score", "PI Focus"]

    # Parse numeric columns (Indonesian format: dot=thousands, comma=decimal)
    def parse_id_number(val):
        if pd.isna(val):
            return np.nan
        s = str(val).strip()
        # Skip clearly non-numeric text entries
        if any(c.isalpha() for c in s.replace("NaN", "")):
            return np.nan
        try:
            # Remove dots (thousands sep), replace comma with dot (decimal)
            s = s.replace(".", "").replace(",", ".")
            return float(s)
        except (ValueError, TypeError):
            return np.nan

    numeric_cols = ["Target Q1", "Target Q2", "Target Q3", "Target Q4", "Realization", "Score"]
    for col in numeric_cols:
        df[col] = df[col].apply(parse_id_number)

    df["No"] = pd.to_numeric(df["No"], errors="coerce").astype("Int64")
    df["PI Focus"] = df["PI Focus"].fillna("NO").astype(str).str.strip().str.upper()
    return df


df = load_data()

# ── Helper Functions ─────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif", color="#cbd5e1"),
    margin=dict(l=40, r=30, t=50, b=40),
    legend=dict(
        bgcolor="rgba(30,41,59,0.6)",
        bordercolor="rgba(99,102,241,0.2)",
        borderwidth=1,
        font=dict(size=11)
    ),
    xaxis=dict(gridcolor="rgba(99,102,241,0.08)", zerolinecolor="rgba(99,102,241,0.15)"),
    yaxis=dict(gridcolor="rgba(99,102,241,0.08)", zerolinecolor="rgba(99,102,241,0.15)"),
)

COLORS = {
    "primary": "#6366f1",
    "secondary": "#a78bfa",
    "accent": "#22d3ee",
    "success": "#34d399",
    "warning": "#fbbf24",
    "danger": "#f87171",
    "q1": "#6366f1",
    "q2": "#8b5cf6",
    "q3": "#a78bfa",
    "q4": "#c4b5fd",
    "realization": "#22d3ee",
}


def safe_pct(real, target):
    """Compute achievement percentage safely."""
    if pd.isna(real) or pd.isna(target) or target == 0:
        return None
    return (real / target) * 100


def get_achievement_color(pct):
    if pct is None:
        return "#64748b"
    if pct >= 100:
        return COLORS["success"]
    if pct >= 75:
        return COLORS["warning"]
    return COLORS["danger"]


def get_achievement_label(pct):
    if pct is None:
        return "N/A"
    if pct >= 100:
        return "✅ Achieved"
    if pct >= 75:
        return "⚠️ On Track"
    return "❌ Below Target"


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 1.5rem 0;">
        <div style="font-size: 2.5rem; margin-bottom: 0.3rem;">🎓</div>
        <div style="color: #a5b4fc; font-weight: 800; font-size: 1.15rem; letter-spacing: -0.3px;">
            PGSD Dashboard
        </div>
        <div style="color: #64748b; font-size: 0.75rem; font-weight: 500;">
            Performance Indicator 2026
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Quarter selection
    selected_quarter = st.selectbox(
        "📅 Pilih Kuartal Perbandingan",
        options=["Q1", "Q2", "Q3", "Q4"],
        index=3,
        help="Pilih kuartal target untuk dibandingkan dengan realisasi."
    )
    quarter_col = f"Target {selected_quarter}"

    # PI Focus filter
    focus_filter = st.radio(
        "🎯 Filter PI Focus",
        options=["Semua", "YES (Fokus)", "NO"],
        index=0,
        help="Filter indikator berdasarkan status PI Focus."
    )

    # Category filter based on keyword grouping
    categories = {
        "Semua Kategori": None,
        "🎓 Students & Enrollment": ["Student", "Intake", "Active", "NR Students", "Graduation"],
        "💰 Revenue & Finance": ["Revenue", "revenue"],
        "🤝 Partnership": ["Partnership", "partner"],
        "📚 Research & Publication": ["SCOPUS", "Citation", "Research", "publication", "paper", "IP(s)", "MULTIDIS"],
        "🌐 International": ["International", "Inbound", "Outbound"],
        "👩‍🏫 Employment & Career": ["Employment", "Entrepreneur", "Employability"],
        "📊 Others": None
    }

    selected_category = st.selectbox(
        "📂 Kategori Indikator",
        options=list(categories.keys()),
        index=0,
    )

    st.markdown("---")
    st.markdown("""
    <div style="padding: 0.8rem; background: rgba(99,102,241,0.08); border-radius: 10px;
                border: 1px solid rgba(99,102,241,0.15); margin-top: 0.5rem;">
        <div style="color: #a5b4fc; font-weight: 700; font-size: 0.82rem; margin-bottom: 0.5rem;">
            ℹ️ Petunjuk
        </div>
        <div style="color: #94a3b8; font-size: 0.74rem; line-height: 1.5;">
            • Pilih kuartal untuk membandingkan target vs realisasi<br>
            • Gunakan filter untuk mempersempit indikator<br>
            • Hover pada grafik untuk detail data<br>
            • Scroll tabel untuk melihat semua kolom
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Apply Filters ────────────────────────────────────────────────────────────
filtered_df = df.copy()

if focus_filter == "YES (Fokus)":
    filtered_df = filtered_df[filtered_df["PI Focus"] == "YES"]
elif focus_filter == "NO":
    filtered_df = filtered_df[filtered_df["PI Focus"] == "NO"]

if selected_category != "Semua Kategori" and selected_category != "📊 Others":
    keywords = categories[selected_category]
    if keywords:
        mask = filtered_df["Performance Indicator"].str.contains("|".join(keywords), case=False, na=False)
        filtered_df = filtered_df[mask]
elif selected_category == "📊 Others":
    all_keywords = []
    for k, v in categories.items():
        if v:
            all_keywords.extend(v)
    mask = ~filtered_df["Performance Indicator"].str.contains("|".join(all_keywords), case=False, na=False)
    filtered_df = filtered_df[mask]


# ── Hero Banner ──────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-banner">
    <h1>📊 Performance Indicator Dashboard</h1>
    <p>Jurusan Pendidikan Guru Sekolah Dasar (PGSD) — Tahun 2026 &nbsp;|&nbsp;
    Kuartal Aktif: <strong>{selected_quarter}</strong> &nbsp;|&nbsp;
    Menampilkan <strong>{len(filtered_df)}</strong> dari {len(df)} indikator</p>
</div>
""", unsafe_allow_html=True)


# ── KPI Summary Cards ───────────────────────────────────────────────────────
# Compute KPIs from filtered data that has both target and realization
comparison_df = filtered_df.dropna(subset=[quarter_col, "Realization"]).copy()
comparison_df["Achievement %"] = comparison_df.apply(
    lambda r: safe_pct(r["Realization"], r[quarter_col]), axis=1
)
valid_comparison = comparison_df.dropna(subset=["Achievement %"])

total_indicators = len(filtered_df)
measurable = len(valid_comparison)
achieved_count = len(valid_comparison[valid_comparison["Achievement %"] >= 100]) if len(valid_comparison) > 0 else 0
avg_achievement = valid_comparison["Achievement %"].mean() if len(valid_comparison) > 0 else 0
pi_focus_count = len(filtered_df[filtered_df["PI Focus"] == "YES"])

avg_color = "kpi-green" if avg_achievement >= 100 else ("kpi-yellow" if avg_achievement >= 75 else "kpi-red")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total Indikator</div>
        <div class="kpi-value kpi-blue">{total_indicators}</div>
        <div class="kpi-sub" style="color:#64748b;">ditampilkan</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Terukur di {selected_quarter}</div>
        <div class="kpi-value" style="color:#a78bfa;">{measurable}</div>
        <div class="kpi-sub" style="color:#64748b;">memiliki target & realisasi</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Target Tercapai</div>
        <div class="kpi-value kpi-green">{achieved_count}</div>
        <div class="kpi-sub kpi-green">≥ 100% realisasi</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Rata-rata Capaian</div>
        <div class="kpi-value {avg_color}">{avg_achievement:.1f}%</div>
        <div class="kpi-sub" style="color:#64748b;">dari target {selected_quarter}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">PI Focus</div>
        <div class="kpi-value" style="color:#fbbf24;">{pi_focus_count}</div>
        <div class="kpi-sub" style="color:#64748b;">prioritas tinggi</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)


# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Perbandingan Target vs Realisasi",
    "📈 Analisis Kuartal",
    "🎯 PI Focus Indicators",
    "📋 Data Lengkap",
])

# ━━ TAB 1: Target vs Realization Comparison ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    st.markdown(f'<div class="section-header">📊 Target {selected_quarter} vs Realisasi</div>',
                unsafe_allow_html=True)

    if len(valid_comparison) == 0:
        st.warning(f"Tidak ada indikator yang memiliki target {selected_quarter} dan realisasi secara bersamaan.")
    else:
        # Shorten indicator names for display
        chart_df = valid_comparison.copy()
        chart_df["Short Name"] = chart_df["Performance Indicator"].apply(
            lambda x: (x[:55] + "…") if len(str(x)) > 55 else x
        )

        # ── Horizontal bar chart: Target vs Realization ──
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            y=chart_df["Short Name"],
            x=chart_df[quarter_col],
            name=f"Target {selected_quarter}",
            orientation="h",
            marker=dict(color=COLORS["q1"], line=dict(width=0)),
            opacity=0.85,
            text=chart_df[quarter_col].apply(lambda v: f"{v:,.2f}"),
            textposition="auto",
            textfont=dict(size=10),
        ))
        fig_bar.add_trace(go.Bar(
            y=chart_df["Short Name"],
            x=chart_df["Realization"],
            name="Realisasi",
            orientation="h",
            marker=dict(color=COLORS["realization"], line=dict(width=0)),
            opacity=0.85,
            text=chart_df["Realization"].apply(lambda v: f"{v:,.2f}"),
            textposition="auto",
            textfont=dict(size=10),
        ))

        fig_bar.update_layout(
            **PLOTLY_LAYOUT,
            barmode="group",
            height=max(450, len(chart_df) * 55),
            title=dict(text=f"Target {selected_quarter} vs Realisasi", font=dict(size=16, color="#e2e8f0")),
            yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # ── Achievement gauge overview ──
        st.markdown(f'<div class="section-header">🏆 Persentase Capaian per Indikator ({selected_quarter})</div>',
                    unsafe_allow_html=True)

        chart_df_sorted = chart_df.sort_values("Achievement %", ascending=True)
        colors_bar = [get_achievement_color(v) for v in chart_df_sorted["Achievement %"]]

        fig_pct = go.Figure(go.Bar(
            y=chart_df_sorted["Short Name"],
            x=chart_df_sorted["Achievement %"],
            orientation="h",
            marker=dict(color=colors_bar, line=dict(width=0)),
            text=chart_df_sorted["Achievement %"].apply(lambda v: f"{v:.1f}%"),
            textposition="outside",
            textfont=dict(size=10, color="#e2e8f0"),
        ))

        fig_pct.add_vline(x=100, line_dash="dash", line_color="#fbbf24", line_width=1.5,
                          annotation_text="Target 100%",
                          annotation_font=dict(color="#fbbf24", size=10))
        fig_pct.update_layout(
            **PLOTLY_LAYOUT,
            height=max(450, len(chart_df_sorted) * 50),
            title=dict(text="Achievement Rate (%)", font=dict(size=16, color="#e2e8f0")),
            xaxis=dict(title="Achievement %", range=[0, max(chart_df_sorted["Achievement %"].max() * 1.2, 120)]),
            yaxis=dict(tickfont=dict(size=10)),
            showlegend=False,
        )
        st.plotly_chart(fig_pct, use_container_width=True)


# ━━ TAB 2: Quarterly Analysis ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    st.markdown('<div class="section-header">📈 Tren Target per Kuartal</div>', unsafe_allow_html=True)

    # Let users select specific indicators
    indicator_options = filtered_df["Performance Indicator"].tolist()
    selected_indicators = st.multiselect(
        "Pilih indikator untuk analisis kuartal:",
        options=indicator_options,
        default=indicator_options[:5] if len(indicator_options) >= 5 else indicator_options,
        help="Pilih satu atau lebih indikator untuk melihat tren target Q1–Q4."
    )

    if selected_indicators:
        sel_df = filtered_df[filtered_df["Performance Indicator"].isin(selected_indicators)].copy()

        # Melt for quarterly trend
        q_cols = ["Target Q1", "Target Q2", "Target Q3", "Target Q4"]
        available_q = [c for c in q_cols if sel_df[c].notna().any()]

        if available_q:
            melt_df = sel_df.melt(
                id_vars=["No", "Performance Indicator", "Realization"],
                value_vars=available_q,
                var_name="Quarter",
                value_name="Target Value"
            ).dropna(subset=["Target Value"])
            melt_df["Quarter Label"] = melt_df["Quarter"].str.replace("Target ", "")
            melt_df["Short Name"] = melt_df["Performance Indicator"].apply(
                lambda x: (x[:50] + "…") if len(str(x)) > 50 else x
            )

            fig_trend = px.line(
                melt_df,
                x="Quarter Label",
                y="Target Value",
                color="Short Name",
                markers=True,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_trend.update_traces(line=dict(width=2.5), marker=dict(size=8))
            fig_trend.update_layout(
                **PLOTLY_LAYOUT,
                height=500,
                title=dict(text="Tren Target Kuartal (Q1 → Q4)", font=dict(size=16, color="#e2e8f0")),
                xaxis_title="Kuartal",
                yaxis_title="Nilai Target",
                legend=dict(orientation="h", yanchor="top", y=-0.15, font=dict(size=10)),
            )
            st.plotly_chart(fig_trend, use_container_width=True)

            # ── Radar chart for selected indicators ──
            st.markdown('<div class="section-header">🕸️ Radar: Target Q4 vs Realisasi (Normalized)</div>',
                        unsafe_allow_html=True)

            radar_df = sel_df.dropna(subset=["Target Q4", "Realization"]).copy()
            if len(radar_df) >= 3:
                radar_df["Short Name"] = radar_df["Performance Indicator"].apply(
                    lambda x: (x[:35] + "…") if len(str(x)) > 35 else x
                )
                max_val = radar_df[["Target Q4", "Realization"]].max().max()
                if max_val > 0:
                    radar_df["T_norm"] = radar_df["Target Q4"] / max_val * 100
                    radar_df["R_norm"] = radar_df["Realization"] / max_val * 100

                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=radar_df["T_norm"].tolist() + [radar_df["T_norm"].iloc[0]],
                        theta=radar_df["Short Name"].tolist() + [radar_df["Short Name"].iloc[0]],
                        fill="toself",
                        name="Target Q4",
                        line=dict(color=COLORS["primary"], width=2),
                        fillcolor="rgba(99,102,241,0.15)",
                    ))
                    fig_radar.add_trace(go.Scatterpolar(
                        r=radar_df["R_norm"].tolist() + [radar_df["R_norm"].iloc[0]],
                        theta=radar_df["Short Name"].tolist() + [radar_df["Short Name"].iloc[0]],
                        fill="toself",
                        name="Realisasi",
                        line=dict(color=COLORS["realization"], width=2),
                        fillcolor="rgba(34,211,238,0.12)",
                    ))
                    fig_radar.update_layout(
                        **PLOTLY_LAYOUT,
                        height=500,
                        polar=dict(
                            bgcolor="rgba(0,0,0,0)",
                            radialaxis=dict(visible=True, gridcolor="rgba(99,102,241,0.1)", color="#64748b"),
                            angularaxis=dict(gridcolor="rgba(99,102,241,0.1)", color="#94a3b8",
                                             tickfont=dict(size=9)),
                        ),
                        title=dict(text="Radar Comparison (Normalized)", font=dict(size=16, color="#e2e8f0")),
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
            else:
                st.info("Pilih minimal 3 indikator yang memiliki Target Q4 dan Realisasi untuk radar chart.")
        else:
            st.info("Indikator terpilih tidak memiliki target kuartal numerik.")
    else:
        st.info("Pilih minimal satu indikator di atas.")

    # ── Distribution of Scores ──
    st.markdown('<div class="section-header">📊 Distribusi Skor</div>', unsafe_allow_html=True)
    score_df = filtered_df.dropna(subset=["Score"])
    if len(score_df) > 0:
        fig_hist = px.histogram(
            score_df, x="Score", nbins=10,
            color_discrete_sequence=[COLORS["secondary"]],
            labels={"Score": "Skor", "count": "Jumlah"},
        )
        fig_hist.update_layout(
            **PLOTLY_LAYOUT,
            height=350,
            title=dict(text="Distribusi Skor Indikator", font=dict(size=15, color="#e2e8f0")),
            bargap=0.1,
        )
        fig_hist.update_traces(marker_line_width=0, opacity=0.85)
        st.plotly_chart(fig_hist, use_container_width=True)


# ━━ TAB 3: PI Focus Indicators ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    st.markdown('<div class="section-header">🎯 Indikator PI Focus (Prioritas Tinggi)</div>',
                unsafe_allow_html=True)

    focus_df = df[df["PI Focus"] == "YES"].copy()

    if len(focus_df) == 0:
        st.info("Tidak ada indikator dengan PI Focus = YES.")
    else:
        # Detailed cards for each focus indicator
        for _, row in focus_df.iterrows():
            target_val = row[quarter_col]
            real_val = row["Realization"]
            pct = safe_pct(real_val, target_val)
            color = get_achievement_color(pct)
            label = get_achievement_label(pct)
            pct_text = f"{pct:.1f}%" if pct is not None else "N/A"
            target_text = f"{target_val:,.2f}" if pd.notna(target_val) else "—"
            real_text = f"{real_val:,.2f}" if pd.notna(real_val) else "—"
            score_text = f"{row['Score']:,.2f}" if pd.notna(row['Score']) else "—"

            st.markdown(f"""
            <div style="background: rgba(30,41,59,0.7); border: 1px solid rgba(99,102,241,0.15);
                        border-left: 4px solid {color}; border-radius: 12px;
                        padding: 1.2rem 1.5rem; margin-bottom: 0.8rem;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.15);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.8rem;">
                    <div style="flex: 1; min-width: 250px;">
                        <div style="color: #e2e8f0; font-weight: 700; font-size: 0.95rem; margin-bottom: 0.4rem;">
                            #{int(row['No'])} — {row['Performance Indicator']}
                        </div>
                        <div style="color: #64748b; font-size: 0.78rem;">Skor: {score_text}</div>
                    </div>
                    <div style="display: flex; gap: 1.5rem; align-items: center; flex-wrap: wrap;">
                        <div style="text-align: center;">
                            <div style="color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px;">
                                Target {selected_quarter}</div>
                            <div style="color: #a5b4fc; font-size: 1.1rem; font-weight: 700;">{target_text}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px;">
                                Realisasi</div>
                            <div style="color: #22d3ee; font-size: 1.1rem; font-weight: 700;">{real_text}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px;">
                                Capaian</div>
                            <div style="color: {color}; font-size: 1.1rem; font-weight: 700;">{pct_text}</div>
                        </div>
                        <div style="font-size: 0.82rem;">{label}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Donut chart for focus indicators achievement
        focus_comp = focus_df.copy()
        focus_comp["Ach"] = focus_comp.apply(lambda r: safe_pct(r["Realization"], r[quarter_col]), axis=1)
        focus_valid = focus_comp.dropna(subset=["Ach"])

        if len(focus_valid) > 0:
            achieved = len(focus_valid[focus_valid["Ach"] >= 100])
            not_achieved = len(focus_valid) - achieved
            no_data = len(focus_comp) - len(focus_valid)

            fig_donut = go.Figure(go.Pie(
                labels=["Tercapai ≥100%", "Belum Tercapai", "Data Belum Tersedia"],
                values=[achieved, not_achieved, no_data],
                hole=0.6,
                marker=dict(colors=[COLORS["success"], COLORS["danger"], "#475569"],
                            line=dict(width=2, color="#1e293b")),
                textinfo="label+value",
                textfont=dict(size=12),
            ))
            fig_donut.update_layout(
                **PLOTLY_LAYOUT,
                height=400,
                title=dict(text=f"Status PI Focus — {selected_quarter}",
                           font=dict(size=16, color="#e2e8f0")),
                annotations=[dict(text=f"{achieved}/{len(focus_comp)}", x=0.5, y=0.5,
                                  font=dict(size=28, color="#e2e8f0", family="Plus Jakarta Sans"),
                                  showarrow=False)],
            )
            st.plotly_chart(fig_donut, use_container_width=True)


# ━━ TAB 4: Full Data Table ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab4:
    st.markdown('<div class="section-header">📋 Tabel Data Lengkap</div>', unsafe_allow_html=True)

    display_df = filtered_df.copy()
    display_df["Achievement %"] = display_df.apply(
        lambda r: safe_pct(r["Realization"], r[quarter_col]), axis=1
    )
    display_df["Status"] = display_df["Achievement %"].apply(get_achievement_label)

    # Search
    search_term = st.text_input("🔍 Cari indikator...", placeholder="Ketik kata kunci...")
    if search_term:
        display_df = display_df[
            display_df["Performance Indicator"].str.contains(search_term, case=False, na=False)
        ]

    st.markdown(f"Menampilkan **{len(display_df)}** indikator")

    # Format for display
    show_cols = ["No", "Performance Indicator", "Target Q1", "Target Q2", "Target Q3", "Target Q4",
                 "Realization", "Score", "PI Focus", "Achievement %", "Status"]
    table_df = display_df[show_cols].copy()

    st.dataframe(
        table_df.style.format({
            "Target Q1": lambda v: f"{v:,.2f}" if pd.notna(v) else "—",
            "Target Q2": lambda v: f"{v:,.2f}" if pd.notna(v) else "—",
            "Target Q3": lambda v: f"{v:,.2f}" if pd.notna(v) else "—",
            "Target Q4": lambda v: f"{v:,.2f}" if pd.notna(v) else "—",
            "Realization": lambda v: f"{v:,.2f}" if pd.notna(v) else "—",
            "Score": lambda v: f"{v:,.2f}" if pd.notna(v) else "—",
            "Achievement %": lambda v: f"{v:.1f}%" if pd.notna(v) else "—",
        }).applymap(
            lambda v: "color: #34d399" if v == "✅ Achieved" else (
                "color: #fbbf24" if v == "⚠️ On Track" else (
                    "color: #f87171" if v == "❌ Below Target" else ""
                )), subset=["Status"]
        ),
        use_container_width=True,
        height=600,
    )

    # Download button
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Data (CSV)",
        data=csv,
        file_name="pgsd_performance_2026.csv",
        mime="text/csv",
    )


# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem 0 0.5rem 0;">
    <div style="color: #475569; font-size: 0.78rem; font-weight: 500;">
        🎓 PGSD Performance Dashboard 2026 &nbsp;|&nbsp;
        Built with Streamlit & Plotly &nbsp;|&nbsp;
        Data: Report Realization Pendidikan Guru Sekolah Dasar
    </div>
</div>
""", unsafe_allow_html=True)
