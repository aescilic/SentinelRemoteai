# dashboard.py - SentinelRemote Security Operations Dashboard
# Streamlit-based visualization for insider threat monitoring
# usage: python -m streamlit run dashboard.py

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import config
from datetime import datetime
import json
import math

# ═══════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="SentinelRemote | Security Operations Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════
# PREMIUM DARK THEME CSS
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* ── Global ── */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0e1a 0%, #0d1321 40%, #111827 100%);
        color: #e2e8f0;
    }
    
    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%) !important;
        border-right: 1px solid rgba(99, 102, 241, 0.15) !important;
    }
    section[data-testid="stSidebar"] * {
        color: #c7d2fe !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stRadio label {
        color: #a5b4fc !important;
        font-weight: 500;
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 1.2px;
    }
    
    /* ── Headings ── */
    h1 { color: #f1f5f9 !important; font-weight: 700 !important; }
    h2 { color: #e2e8f0 !important; font-weight: 600 !important; }
    h3 { color: #cbd5e1 !important; font-weight: 600 !important; }
    h4 { color: #94a3b8 !important; font-weight: 500 !important; text-transform: uppercase; font-size: 0.85rem !important; letter-spacing: 0.8px; }
    
    /* ── Metric Cards ── */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, rgba(30,27,75,0.6) 0%, rgba(15,23,42,0.8) 100%);
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 16px;
        padding: 20px 24px;
        backdrop-filter: blur(20px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
    }
    div[data-testid="metric-container"]:hover {
        border-color: rgba(99,102,241,0.5);
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(99,102,241,0.15), inset 0 1px 0 rgba(255,255,255,0.08);
    }
    div[data-testid="metric-container"] > div > div > div {
        color: #94a3b8 !important;
        font-weight: 600;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div[data-testid="metric-container"] > div > div > div:nth-child(2) {
        color: #f1f5f9 !important;
        font-size: 2rem;
        font-weight: 800;
        margin-top: 6px;
        font-feature-settings: 'tnum';
    }
    
    /* ── DataFrames ── */
    .stDataFrame {
        background: rgba(15,23,42,0.6);
        border: 1px solid rgba(99,102,241,0.15);
        border-radius: 12px;
        padding: 4px;
        backdrop-filter: blur(10px);
    }
    
    /* ── Plotly Charts ── */
    .js-plotly-plot {
        border-radius: 12px;
    }
    
    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
        color: white;
        border-radius: 10px;
        border: none;
        font-weight: 600;
        padding: 0.5rem 1.2rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(79,70,229,0.3);
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%);
        box-shadow: 0 6px 20px rgba(99,102,241,0.4);
        transform: translateY(-1px);
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(15,23,42,0.5);
        border-radius: 12px;
        padding: 4px;
        border: 1px solid rgba(99,102,241,0.1);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        color: #94a3b8;
        font-weight: 500;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
        color: white !important;
        font-weight: 600;
    }
    
    /* ── Expanders ── */
    .streamlit-expanderHeader {
        background: rgba(30,27,75,0.4);
        border: 1px solid rgba(99,102,241,0.15);
        border-radius: 10px;
        color: #c7d2fe !important;
    }
    
    /* ── Custom Card Component ── */
    .sentinel-card {
        background: linear-gradient(145deg, rgba(30,27,75,0.5) 0%, rgba(15,23,42,0.7) 100%);
        border: 1px solid rgba(99,102,241,0.15);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(20px);
        box-shadow: 0 4px 24px rgba(0,0,0,0.2);
        margin-bottom: 16px;
    }
    .sentinel-card:hover {
        border-color: rgba(99,102,241,0.3);
    }

    /* ── Status Badges ── */
    .badge-critical {
        background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(185,28,28,0.2));
        color: #fca5a5;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid rgba(239,68,68,0.3);
        display: inline-block;
    }
    .badge-review {
        background: linear-gradient(135deg, rgba(245,158,11,0.2), rgba(180,83,9,0.2));
        color: #fcd34d;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid rgba(245,158,11,0.3);
        display: inline-block;
    }
    .badge-normal {
        background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(5,150,105,0.2));
        color: #6ee7b7;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid rgba(16,185,129,0.3);
        display: inline-block;
    }
    
    /* ── Header bar ── */
    .sentinel-header {
        background: linear-gradient(135deg, rgba(30,27,75,0.7), rgba(15,23,42,0.9));
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        backdrop-filter: blur(20px);
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    }
    .sentinel-header h2 {
        margin: 0 !important;
        font-size: 1.1rem !important;
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }
    .sentinel-header .meta {
        color: #64748b;
        font-size: 0.82rem;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* ── Threat level indicator ── */
    .threat-level {
        text-align: center;
        padding: 16px;
        border-radius: 16px;
        margin-bottom: 8px;
    }
    .threat-level.elevated {
        background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(185,28,28,0.1));
        border: 1px solid rgba(239,68,68,0.3);
    }
    .threat-level.moderate {
        background: linear-gradient(135deg, rgba(245,158,11,0.15), rgba(180,83,9,0.1));
        border: 1px solid rgba(245,158,11,0.3);
    }
    .threat-level.low {
        background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(5,150,105,0.1));
        border: 1px solid rgba(16,185,129,0.3);
    }
    .threat-level h1 {
        font-size: 2.5rem !important;
        margin: 0 !important;
        line-height: 1.2;
    }
    .threat-level p {
        margin: 4px 0 0 0;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
    }
    
    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0f172a; }
    ::-webkit-scrollbar-thumb { background: #4f46e5; border-radius: 3px; }
    
    /* ── Hide streamlit branding ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    
    /* ── Login page ── */
    .login-container {
        max-width: 420px;
        margin: 0 auto;
        padding: 48px 40px;
        background: linear-gradient(145deg, rgba(30,27,75,0.7), rgba(15,23,42,0.9));
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 24px;
        backdrop-filter: blur(30px);
        box-shadow: 0 25px 50px rgba(0,0,0,0.5), 0 0 80px rgba(99,102,241,0.08);
    }
    .login-logo {
        text-align: center;
        margin-bottom: 32px;
    }
    .login-logo h1 {
        font-size: 1.8rem !important;
        background: linear-gradient(135deg, #818cf8, #6366f1, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 8px 0 4px 0 !important;
    }
    .login-logo p {
        color: #64748b;
        font-size: 0.85rem;
        margin: 0;
    }
    .login-logo .shield {
        font-size: 3rem;
        display: block;
        margin-bottom: 4px;
    }
    
    /* ── Input fields for login ── */
    .stTextInput > div > div > input {
        background: rgba(15,23,42,0.8) !important;
        border: 1px solid rgba(99,102,241,0.2) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        padding: 12px 16px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
    }
    .stTextInput label {
        color: #94a3b8 !important;
        font-weight: 500;
        font-size: 0.85rem;
    }
    
    /* ── Selectbox ── */
    .stSelectbox > div > div {
        background: rgba(15,23,42,0.8) !important;
        border: 1px solid rgba(99,102,241,0.2) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
    }
    
    /* ── Radio buttons in sidebar ── */
    .stRadio > div {
        gap: 2px;
    }

</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════
CHART_BG = "rgba(0,0,0,0)"
CHART_GRID = "rgba(99,102,241,0.08)"
CHART_TEXT = "#94a3b8"

def styled_chart_layout(fig, height=380):
    """applies consistent dark theme to all plotly charts"""
    fig.update_layout(
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        font=dict(family="Inter", color=CHART_TEXT, size=12),
        margin=dict(l=16, r=16, t=40, b=16),
        height=height,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c7d2fe", size=11),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        xaxis=dict(gridcolor=CHART_GRID, zerolinecolor=CHART_GRID),
        yaxis=dict(gridcolor=CHART_GRID, zerolinecolor=CHART_GRID),
    )
    return fig


def risk_badge(level):
    """returns HTML badge for risk level"""
    if level == "CRITICAL":
        return '<span class="badge-critical">🔴 CRITICAL</span>'
    elif level == "REVIEW":
        return '<span class="badge-review">🟡 REVIEW</span>'
    else:
        return '<span class="badge-normal">🟢 CLEARED</span>'


def category_icon(cat):
    """returns icon for alert category"""
    icons = {
        "TEMPORAL": "🕐",
        "VOLUMETRIC": "📊",
        "BEHAVIORAL": "🧠",
        "COMBINED": "⚡",
        "SHADOW_AI": "🤖",
    }
    return icons.get(cat, "📌")


# ═══════════════════════════════════════════════════════════
# LOGIN SYSTEM
# ═══════════════════════════════════════════════════════════
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<div style='height: 60px;'></div>", unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns([1.2, 1, 1.2])
    with col_m:
        st.markdown("""
        <div class="login-container">
            <div class="login-logo">
                <span class="shield">🛡️</span>
                <h1>SentinelRemote</h1>
                <p>Security Operations Center</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        if st.button("🔐  Authenticate", use_container_width=True):
            if username == "admin" and password == "admin":
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("⛔ Authentication failed. Access denied.")
        
        st.markdown("""
        <div style='text-align: center; margin-top: 24px;'>
            <p style='font-size: 0.75rem; color: #475569; margin: 4px 0;'>🔒 Encrypted Connection Active</p>
            <p style='font-size: 0.7rem; color: #334155; margin: 0;'>Internal Network Access Required</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()


# ═══════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════
@st.cache_data(ttl=60)
def load_data():
    """loads alerts, baselines and events from the SQLite database"""
    conn = sqlite3.connect(config.DB_PATH)
    try:
        alerts = pd.read_sql("SELECT * FROM " + config.ALERT_TABLE, conn)
        baselines = pd.read_sql("SELECT * FROM " + config.BASELINE_TABLE, conn)
        events = pd.read_sql("SELECT * FROM security_events", conn)
        if not alerts.empty:
            alerts["timestamp"] = pd.to_datetime(alerts["timestamp"])
        if not events.empty:
            events["timestamp"] = pd.to_datetime(events["timestamp"])
    except Exception:
        alerts, baselines, events = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    conn.close()
    return alerts, baselines, events

alerts_df, baselines_df, events_df = load_data()


# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════
st.sidebar.markdown("""
<div style='text-align: center; padding: 16px 0 20px 0; border-bottom: 1px solid rgba(99,102,241,0.15);'>
    <span style='font-size: 2rem;'>🛡️</span>
    <h2 style='margin: 4px 0 0 0 !important; font-size: 1.3rem !important; 
    background: linear-gradient(135deg, #818cf8, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
    SentinelRemote</h2>
    <p style='color: #64748b !important; font-size: 0.7rem; margin: 2px 0 0 0; letter-spacing: 1.5px; text-transform: uppercase;'>
    Security Operations</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<br>", unsafe_allow_html=True)

menu_selection = st.sidebar.radio(
    "NAVIGATION",
    ["📊 Overview", "🚨 Threat Intelligence", "👥 User Profiles", "🤖 Shadow AI Monitor", "⚙️ System Config"],
)

st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='font-size: 0.7rem; letter-spacing: 1.2px; color: #475569 !important;'>FILTERS</p>", unsafe_allow_html=True)

if not baselines_df.empty:
    all_users = ["All Users"] + sorted(list(baselines_df["username"].unique()))
else:
    all_users = ["All Users"]
selected_user = st.sidebar.selectbox("Target Identity", all_users)

if not alerts_df.empty:
    risk_levels = ["All Severities"] + list(alerts_df["risk_level"].unique())
else:
    risk_levels = ["All Severities"]
selected_risk = st.sidebar.selectbox("Alert Severity", risk_levels)

st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
if st.sidebar.button("🚪  Logout", use_container_width=True):
    st.session_state["logged_in"] = False
    st.rerun()

st.sidebar.markdown("""
<div style='position: fixed; bottom: 16px; left: 16px; right: 16px;'>
    <p style='font-size: 0.65rem; color: #334155 !important; text-align: center;'>
    SentinelRemote v1.0<br>Graduation Project © 2025</p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# HEADER BAR
# ═══════════════════════════════════════════════════════════
current_time = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
st.markdown(f"""
<div class="sentinel-header">
    <h2>🛡️ Security Operations Center — Dashboard</h2>
    <div class="meta">OPERATOR: admin &nbsp;│&nbsp; {current_time} &nbsp;│&nbsp; SESSION ACTIVE</div>
</div>
""", unsafe_allow_html=True)

if alerts_df.empty or baselines_df.empty:
    st.warning("⚠️ No detection data found. Please run `python run_detection.py` first to generate results.")
    st.stop()


# ═══════════════════════════════════════════════════════════
# APPLY FILTERS
# ═══════════════════════════════════════════════════════════
f_alerts = alerts_df.copy()
f_events = events_df.copy()
f_base = baselines_df.copy()

if selected_user != "All Users":
    f_alerts = f_alerts[f_alerts["username"] == selected_user]
    f_events = f_events[f_events["username"] == selected_user]
    f_base = f_base[f_base["username"] == selected_user]

if selected_risk != "All Severities":
    f_alerts = f_alerts[f_alerts["risk_level"] == selected_risk]


# ═══════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ═══════════════════════════════════════════════════════════
if menu_selection == "📊 Overview":

    # ── Threat Level Assessment ──
    critical_count = len(alerts_df[alerts_df["risk_level"] == "CRITICAL"])
    review_count = len(alerts_df[alerts_df["risk_level"] == "REVIEW"])
    normal_count = len(alerts_df[alerts_df["risk_level"] == "NORMAL"])
    shadow_ai_count = len(alerts_df[alerts_df["category"] == "SHADOW_AI"])
    total_alerts = len(alerts_df)

    if critical_count > 0:
        threat_class = "elevated"
        threat_label = "ELEVATED"
        threat_color = "#ef4444"
    elif review_count > 3:
        threat_class = "moderate"
        threat_label = "MODERATE"
        threat_color = "#f59e0b"
    else:
        threat_class = "low"
        threat_label = "LOW"
        threat_color = "#10b981"

    # ── Top Row: Threat Level + Metrics ──
    col_threat, col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns([1.2, 1, 1, 1, 1, 1])

    with col_threat:
        st.markdown(f"""
        <div class="threat-level {threat_class}">
            <h1 style="color: {threat_color} !important;">{threat_label}</h1>
            <p style="color: {threat_color};">System Threat Level</p>
        </div>
        """, unsafe_allow_html=True)

    col_m1.metric("Monitored Users", len(baselines_df))
    col_m2.metric("Events Processed", f"{events_df.shape[0]:,}")
    col_m3.metric("Critical Alerts", critical_count)
    col_m4.metric("Review Alerts", review_count)
    col_m5.metric("Shadow AI Hits", shadow_ai_count)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Alert Timeline + Category Distribution ──
    row1_col1, row1_col2 = st.columns([2, 1])

    with row1_col1:
        st.markdown("#### Recent Security Incidents")
        
        if not f_alerts.empty:
            display_df = f_alerts[["timestamp", "username", "risk_level", "category", "reason"]].copy()
            display_df = display_df.sort_values(by="timestamp", ascending=False)
            display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
            
            # apply risk badges
            def format_risk(val):
                if val == "CRITICAL":
                    return "🔴 CRITICAL"
                elif val == "REVIEW":
                    return "⚠️ REVIEW"
                return "✅ CLEARED"
            
            def format_category(val):
                return category_icon(val) + " " + val
            
            display_df["risk_level"] = display_df["risk_level"].apply(format_risk)
            display_df["category"] = display_df["category"].apply(format_category)
            
            display_df.columns = ["Timestamp", "User", "Severity", "Category", "Description"]
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=420,
            )
        else:
            st.info("No incidents matching current filter criteria.")

    with row1_col2:
        st.markdown("#### Alert Distribution")
        
        if not f_alerts.empty:
            # Severity donut chart
            sev_counts = f_alerts["risk_level"].value_counts().reset_index()
            sev_counts.columns = ["Severity", "Count"]
            
            color_map = {"CRITICAL": "#ef4444", "REVIEW": "#f59e0b", "NORMAL": "#10b981"}
            
            fig_donut = px.pie(
                sev_counts, names="Severity", values="Count",
                hole=0.65,
                color="Severity",
                color_discrete_map=color_map,
            )
            fig_donut.update_traces(
                textposition="outside",
                textinfo="label+value",
                textfont=dict(color="#c7d2fe", size=12),
                marker=dict(line=dict(color="#0f172a", width=2)),
            )
            styled_chart_layout(fig_donut, height=200)
            fig_donut.update_layout(showlegend=False, margin=dict(l=8, r=8, t=8, b=8))
            st.plotly_chart(fig_donut, use_container_width=True, key="overview_donut")
        
        # Category breakdown
        if not f_alerts.empty:
            cat_counts = f_alerts["category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            
            cat_colors = {
                "TEMPORAL": "#6366f1",
                "VOLUMETRIC": "#3b82f6",
                "BEHAVIORAL": "#8b5cf6",
                "COMBINED": "#ef4444",
                "SHADOW_AI": "#a78bfa",
            }
            
            fig_cat = px.bar(
                cat_counts, x="Count", y="Category", orientation="h",
                color="Category",
                color_discrete_map=cat_colors,
            )
            fig_cat.update_traces(
                texttemplate="%{x}", textposition="auto",
                textfont=dict(color="white", size=12),
            )
            styled_chart_layout(fig_cat, height=200)
            fig_cat.update_layout(showlegend=False, margin=dict(l=8, r=8, t=8, b=8))
            st.plotly_chart(fig_cat, use_container_width=True, key="overview_categories")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Z-Score Anomaly + Activity Timeline ──
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.markdown("#### Behavioral Anomaly Index — Z-Score Analysis")
        
        if not f_base.empty:
            z_data = f_base[["username", "volume_zscore", "file_ops_zscore", "delete_zscore"]].copy()
            z_melted = z_data.melt(
                id_vars=["username"],
                value_vars=["volume_zscore", "file_ops_zscore", "delete_zscore"],
                var_name="Metric",
                value_name="Z-Score",
            )
            metric_labels = {
                "volume_zscore": "Volume",
                "file_ops_zscore": "File Ops",
                "delete_zscore": "Deletions",
            }
            z_melted["Metric"] = z_melted["Metric"].map(metric_labels)
            
            fig_z = px.bar(
                z_melted, x="username", y="Z-Score", color="Metric",
                barmode="group",
                color_discrete_map={"Volume": "#6366f1", "File Ops": "#3b82f6", "Deletions": "#ef4444"},
            )
            # critical threshold line
            fig_z.add_hline(
                y=3.0, line_dash="dash", line_color="#ef4444", line_width=1.5,
                annotation_text="CRITICAL (Z≥3)", annotation_position="top right",
                annotation_font=dict(color="#fca5a5", size=10),
            )
            fig_z.add_hline(
                y=2.0, line_dash="dot", line_color="#f59e0b", line_width=1,
                annotation_text="REVIEW (Z≥2)", annotation_position="top right",
                annotation_font=dict(color="#fcd34d", size=10),
            )
            styled_chart_layout(fig_z)
            fig_z.update_layout(
                xaxis_title="User Identity",
                yaxis_title="Standard Deviations (σ)",
            )
            st.plotly_chart(fig_z, use_container_width=True, key="overview_zscore")

    with row2_col2:
        st.markdown("#### Activity Timeline — Hourly Distribution")
        
        if not f_events.empty:
            f_events_copy = f_events.copy()
            f_events_copy["hour"] = f_events_copy["timestamp"].dt.hour
            hourly = f_events_copy.groupby(["hour", "action"]).size().reset_index(name="count")
            
            action_colors = {
                "LOGIN": "#10b981", "LOGOUT": "#475569", "READ": "#3b82f6",
                "WRITE": "#f59e0b", "DELETE": "#ef4444", "WEB_VISIT": "#a78bfa",
                "EMAIL": "#06b6d4",
            }
            
            fig_hourly = px.bar(
                hourly, x="hour", y="count", color="action", barmode="stack",
                color_discrete_map=action_colors,
                labels={"hour": "Hour (24H)", "count": "Event Count", "action": "Action"},
            )
            # highlight danger zone (night hours)
            fig_hourly.add_vrect(
                x0=-0.5, x1=6.5,
                fillcolor="rgba(239,68,68,0.06)", layer="below",
                line=dict(color="rgba(239,68,68,0.15)", width=1, dash="dot"),
                annotation_text="⚠️ Off-Hours Zone",
                annotation_position="top left",
                annotation_font=dict(color="#fca5a5", size=10),
            )
            styled_chart_layout(fig_hourly)
            fig_hourly.update_layout(xaxis=dict(dtick=1))
            st.plotly_chart(fig_hourly, use_container_width=True, key="overview_hourly")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Event Scatter Timeline ──
    st.markdown("#### User Activity Correlation Map")
    if not f_events.empty:
        fig_scatter = px.scatter(
            f_events, x="timestamp", y="username", color="action",
            hover_data=["details"],
            color_discrete_map={
                "LOGIN": "#10b981", "LOGOUT": "#475569", "READ": "#3b82f6",
                "WRITE": "#f59e0b", "DELETE": "#ef4444", "WEB_VISIT": "#a78bfa",
                "EMAIL": "#06b6d4",
            },
        )
        fig_scatter.update_traces(marker=dict(size=8, opacity=0.85, line=dict(width=0.5, color="#0f172a")))
        styled_chart_layout(fig_scatter, height=300)
        fig_scatter.update_layout(
            xaxis_title="Timeline",
            yaxis_title="User",
        )
        st.plotly_chart(fig_scatter, use_container_width=True, key="overview_scatter")


# ═══════════════════════════════════════════════════════════
# PAGE: THREAT INTELLIGENCE
# ═══════════════════════════════════════════════════════════
elif menu_selection == "🚨 Threat Intelligence":

    st.markdown("#### Active Threat Analysis")
    st.markdown("<br>", unsafe_allow_html=True)

    if f_alerts.empty:
        st.info("No threat data matching current filters.")
        st.stop()

    # ── Per-User Threat Score Table ──
    user_scores = []
    for user in baselines_df["username"].unique():
        user_alerts = alerts_df[alerts_df["username"] == user]
        crit = len(user_alerts[user_alerts["risk_level"] == "CRITICAL"])
        rev = len(user_alerts[user_alerts["risk_level"] == "REVIEW"])
        score = crit * 10 + rev * 3
        
        user_base = baselines_df[baselines_df["username"] == user].iloc[0]
        max_z = max(user_base["volume_zscore"], user_base["file_ops_zscore"], user_base["delete_zscore"])
        
        if score >= 20:
            risk_tag = "🔴 HIGH RISK"
        elif score >= 5:
            risk_tag = "🟡 MODERATE"
        else:
            risk_tag = "🟢 LOW RISK"
        
        user_scores.append({
            "User": user,
            "Risk Assessment": risk_tag,
            "Threat Score": score,
            "Critical Alerts": crit,
            "Review Alerts": rev,
            "Max Z-Score": round(max_z, 2),
            "Off-Hours Events": int(user_base["off_hours_count"]),
        })
    
    scores_df = pd.DataFrame(user_scores).sort_values("Threat Score", ascending=False)
    
    st.dataframe(scores_df, use_container_width=True, hide_index=True, height=240)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── Alert Details ──
    st.markdown("#### Detailed Alert Feed")
    
    tabs = st.tabs(["🔴 Critical", "🟡 Review", "🟢 Cleared", "📋 All"])
    
    for i, (tab, level) in enumerate(zip(tabs, ["CRITICAL", "REVIEW", "NORMAL", None])):
        with tab:
            if level:
                tab_alerts = f_alerts[f_alerts["risk_level"] == level]
            else:
                tab_alerts = f_alerts
            
            if tab_alerts.empty:
                st.info(f"No {'alerts' if level is None else level.lower() + ' alerts'} found.")
            else:
                for idx, row in tab_alerts.sort_values("timestamp", ascending=False).iterrows():
                    icon = category_icon(row["category"])
                    ts = row["timestamp"].strftime("%Y-%m-%d %H:%M") if hasattr(row["timestamp"], "strftime") else str(row["timestamp"])
                    
                    with st.expander(f"{icon}  [{row['risk_level']}] {row['username']} — {row['category']}  |  {ts}"):
                        st.markdown(f"**Reason:** {row['reason']}")
                        if row.get("details") and row["details"] != "{}":
                            try:
                                details = json.loads(row["details"]) if isinstance(row["details"], str) else row["details"]
                                st.json(details)
                            except Exception:
                                st.code(str(row["details"]))


# ═══════════════════════════════════════════════════════════
# PAGE: USER PROFILES
# ═══════════════════════════════════════════════════════════
elif menu_selection == "👥 User Profiles":

    st.markdown("#### User Behavioral Profiles")
    st.markdown("<br>", unsafe_allow_html=True)

    if f_base.empty:
        st.info("No baseline data available.")
        st.stop()

    for _, user_row in f_base.iterrows():
        uname = user_row["username"]
        user_alerts = alerts_df[alerts_df["username"] == uname]
        crit_c = len(user_alerts[user_alerts["risk_level"] == "CRITICAL"])
        rev_c = len(user_alerts[user_alerts["risk_level"] == "REVIEW"])
        
        if crit_c > 0:
            status_icon = "🔴"
            border_color = "rgba(239,68,68,0.4)"
        elif rev_c > 0:
            status_icon = "🟡"
            border_color = "rgba(245,158,11,0.4)"
        else:
            status_icon = "🟢"
            border_color = "rgba(16,185,129,0.4)"

        with st.expander(f"{status_icon}  {uname}  —  {int(user_row['total_events'])} events  |  {crit_c} critical, {rev_c} review alerts", expanded=(crit_c > 0)):
            
            p_col1, p_col2, p_col3, p_col4 = st.columns(4)
            p_col1.metric("Total Events", int(user_row["total_events"]))
            p_col2.metric("File Operations", int(user_row["total_file_ops"]))
            p_col3.metric("Off-Hours Activity", int(user_row["off_hours_count"]))
            p_col4.metric("Night Activity", int(user_row["deep_night_count"]))
            
            z_col1, z_col2 = st.columns(2)
            
            with z_col1:
                # Z-Score radar chart
                z_labels = ["Volume", "File Ops", "Deletions"]
                z_values = [
                    round(user_row["volume_zscore"], 2),
                    round(user_row["file_ops_zscore"], 2),
                    round(user_row["delete_zscore"], 2),
                ]
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=z_values + [z_values[0]],
                    theta=z_labels + [z_labels[0]],
                    fill="toself",
                    fillcolor="rgba(99,102,241,0.2)",
                    line=dict(color="#6366f1", width=2),
                    name=uname,
                ))
                fig_radar.update_layout(
                    polar=dict(
                        bgcolor="rgba(0,0,0,0)",
                        radialaxis=dict(visible=True, range=[0, max(max(z_values) + 1, 4)], gridcolor=CHART_GRID, color=CHART_TEXT),
                        angularaxis=dict(gridcolor=CHART_GRID, color="#c7d2fe"),
                    ),
                    paper_bgcolor=CHART_BG,
                    font=dict(color=CHART_TEXT),
                    showlegend=False,
                    height=280,
                    margin=dict(l=60, r=60, t=30, b=30),
                    title=dict(text="Z-Score Profile", font=dict(color="#94a3b8", size=13)),
                )
                st.plotly_chart(fig_radar, use_container_width=True, key="profile_radar_" + uname)
            
            with z_col2:
                # File operations breakdown
                file_data = {
                    "Operation": ["Reads", "Writes", "Deletes"],
                    "Count": [int(user_row["file_reads"]), int(user_row["file_writes"]), int(user_row["file_deletes"])],
                }
                fig_file = px.bar(
                    file_data, x="Operation", y="Count",
                    color="Operation",
                    color_discrete_map={"Reads": "#3b82f6", "Writes": "#f59e0b", "Deletes": "#ef4444"},
                )
                fig_file.update_traces(texttemplate="%{y}", textposition="auto", textfont=dict(color="white"))
                styled_chart_layout(fig_file, height=280)
                fig_file.update_layout(
                    showlegend=False,
                    title=dict(text="File Operations Breakdown", font=dict(color="#94a3b8", size=13)),
                )
                st.plotly_chart(fig_file, use_container_width=True, key="profile_fileops_" + uname)


# ═══════════════════════════════════════════════════════════
# PAGE: SHADOW AI MONITOR
# ═══════════════════════════════════════════════════════════
elif menu_selection == "🤖 Shadow AI Monitor":

    st.markdown("#### Shadow AI Usage Monitor")
    st.markdown("""
    <div class="sentinel-card">
        <p style="color: #c7d2fe; margin: 0; font-size: 0.9rem;">
        🤖 <strong>Shadow AI</strong> refers to unauthorized use of generative AI tools (ChatGPT, Claude, Gemini, etc.) 
        by employees without IT/security approval. This module monitors web activity logs for access to restricted AI domains, 
        flagging potential data leakage and compliance violations.
        </p>
    </div>
    """, unsafe_allow_html=True)

    shadow_alerts = f_alerts[f_alerts["category"] == "SHADOW_AI"]

    if shadow_alerts.empty:
        st.success("✅ No unauthorized AI tool usage detected in the current dataset.")
    else:
        s_col1, s_col2, s_col3 = st.columns(3)
        s_col1.metric("Shadow AI Incidents", len(shadow_alerts))
        s_col2.metric("Unique Users", shadow_alerts["username"].nunique())
        
        # extract domains from reasons
        domains_found = []
        for reason in shadow_alerts["reason"]:
            for domain in config.SHADOW_AI_DOMAINS:
                if domain in reason:
                    domains_found.append(domain)
        s_col3.metric("Unique Domains", len(set(domains_found)))

        st.markdown("<br>", unsafe_allow_html=True)
        
        sa_col1, sa_col2 = st.columns(2)
        
        with sa_col1:
            st.markdown("#### Incidents by User")
            user_sa = shadow_alerts.groupby("username").size().reset_index(name="Count")
            fig_sa_user = px.bar(
                user_sa, x="username", y="Count",
                color="Count",
                color_continuous_scale=["#6366f1", "#a78bfa", "#ef4444"],
            )
            fig_sa_user.update_traces(texttemplate="%{y}", textposition="auto", textfont=dict(color="white"))
            styled_chart_layout(fig_sa_user, height=300)
            fig_sa_user.update_layout(coloraxis_showscale=False, xaxis_title="User", yaxis_title="Incidents")
            st.plotly_chart(fig_sa_user, use_container_width=True, key="shadow_user")
        
        with sa_col2:
            st.markdown("#### Detected AI Domains")
            if domains_found:
                domain_counts = pd.Series(domains_found).value_counts().reset_index()
                domain_counts.columns = ["Domain", "Hits"]
                fig_sa_dom = px.pie(
                    domain_counts, names="Domain", values="Hits",
                    hole=0.6,
                    color_discrete_sequence=["#6366f1", "#818cf8", "#a78bfa", "#c4b5fd", "#ddd6fe"],
                )
                fig_sa_dom.update_traces(
                    textposition="outside",
                    textinfo="label+value",
                    textfont=dict(color="#c7d2fe", size=11),
                    marker=dict(line=dict(color="#0f172a", width=2)),
                )
                styled_chart_layout(fig_sa_dom, height=300)
                fig_sa_dom.update_layout(showlegend=False, margin=dict(l=8, r=8, t=8, b=8))
                st.plotly_chart(fig_sa_dom, use_container_width=True, key="shadow_domains")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Shadow AI Incident Log")
        
        for idx, row in shadow_alerts.sort_values("timestamp", ascending=False).iterrows():
            ts = row["timestamp"].strftime("%Y-%m-%d %H:%M") if hasattr(row["timestamp"], "strftime") else str(row["timestamp"])
            with st.expander(f"🤖  {row['username']}  |  {ts}"):
                st.markdown(f"**{row['reason']}**")

    # ── Monitored Domain List ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Restricted AI Domain Blocklist")
    domain_table = pd.DataFrame({
        "Domain": config.SHADOW_AI_DOMAINS,
        "Status": ["🔒 Blocked"] * len(config.SHADOW_AI_DOMAINS),
        "Category": ["Generative AI"] * len(config.SHADOW_AI_DOMAINS),
    })
    st.dataframe(domain_table, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════
# PAGE: SYSTEM CONFIG
# ═══════════════════════════════════════════════════════════
elif menu_selection == "⚙️ System Config":

    st.markdown("#### System Configuration & Detection Parameters")
    st.markdown("<br>", unsafe_allow_html=True)

    cfg_col1, cfg_col2 = st.columns(2)

    with cfg_col1:
        st.markdown("""
        <div class="sentinel-card">
            <h3 style="color: #c7d2fe !important; font-size: 1rem !important; margin-top: 0;">⏰ Time Windows</h3>
            <table style="width: 100%; color: #94a3b8; font-size: 0.85rem;">
                <tr><td>Work Hours</td><td style="text-align: right; color: #e2e8f0; font-family: 'JetBrains Mono', monospace;">""" + str(config.WORK_HOURS_START) + """:00 — """ + str(config.WORK_HOURS_END) + """:00</td></tr>
                <tr><td>Night Hours (Critical)</td><td style="text-align: right; color: #fca5a5; font-family: 'JetBrains Mono', monospace;">""" + str(config.NIGHT_HOURS_START) + """:00 — """ + str(config.NIGHT_HOURS_END) + """:00</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="sentinel-card">
            <h3 style="color: #c7d2fe !important; font-size: 1rem !important; margin-top: 0;">📊 Z-Score Thresholds</h3>
            <table style="width: 100%; color: #94a3b8; font-size: 0.85rem;">
                <tr><td>Critical Threshold</td><td style="text-align: right; color: #fca5a5; font-family: 'JetBrains Mono', monospace;">Z ≥ """ + str(config.ZSCORE_CRITICAL) + """</td></tr>
                <tr><td>Review Threshold</td><td style="text-align: right; color: #fcd34d; font-family: 'JetBrains Mono', monospace;">Z ≥ """ + str(config.ZSCORE_REVIEW) + """</td></tr>
                <tr><td>Combined Escalation</td><td style="text-align: right; color: #a78bfa; font-family: 'JetBrains Mono', monospace;">Z ≥ """ + str(config.COMBINED_THRESHOLD_ZSCORE) + """</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with cfg_col2:
        st.markdown("""
        <div class="sentinel-card">
            <h3 style="color: #c7d2fe !important; font-size: 1rem !important; margin-top: 0;">🔍 Behavioral Rules</h3>
            <table style="width: 100%; color: #94a3b8; font-size: 0.85rem;">
                <tr><td>File Ops Critical</td><td style="text-align: right; color: #fca5a5; font-family: 'JetBrains Mono', monospace;">≥ """ + str(config.FILE_OP_CRITICAL) + """ / hour</td></tr>
                <tr><td>File Ops Review</td><td style="text-align: right; color: #fcd34d; font-family: 'JetBrains Mono', monospace;">≥ """ + str(config.FILE_OP_REVIEW) + """ / hour</td></tr>
                <tr><td>Delete Critical</td><td style="text-align: right; color: #fca5a5; font-family: 'JetBrains Mono', monospace;">≥ """ + str(config.DELETE_CRITICAL) + """ events</td></tr>
                <tr><td>Delete Review</td><td style="text-align: right; color: #fcd34d; font-family: 'JetBrains Mono', monospace;">≥ """ + str(config.DELETE_REVIEW) + """ events</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="sentinel-card">
            <h3 style="color: #c7d2fe !important; font-size: 1rem !important; margin-top: 0;">👤 Account Classifications</h3>
            <table style="width: 100%; color: #94a3b8; font-size: 0.85rem;">
                <tr><td>Suspicious Accounts</td><td style="text-align: right; color: #fca5a5; font-family: 'JetBrains Mono', monospace;">""" + ", ".join(config.SUSPICIOUS_ACCOUNTS) + """</td></tr>
                <tr><td>Whitelisted Accounts</td><td style="text-align: right; color: #6ee7b7; font-family: 'JetBrains Mono', monospace;">""" + ", ".join(config.WHITELISTED_ACCOUNTS) + """</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    # ── Detection Pipeline Info ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Detection Pipeline Architecture")
    
    st.markdown("""
    <div class="sentinel-card" style="text-align: center;">
        <div style="display: flex; justify-content: center; align-items: center; gap: 12px; flex-wrap: wrap; padding: 16px 0;">
            <div style="background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.3); border-radius: 12px; padding: 14px 20px; min-width: 140px;">
                <div style="font-size: 1.5rem;">📥</div>
                <div style="color: #c7d2fe; font-size: 0.8rem; font-weight: 600; margin-top: 4px;">Log Collection</div>
                <div style="color: #64748b; font-size: 0.7rem;">Windows Events</div>
            </div>
            <div style="color: #4f46e5; font-size: 1.2rem;">→</div>
            <div style="background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.3); border-radius: 12px; padding: 14px 20px; min-width: 140px;">
                <div style="font-size: 1.5rem;">🗄️</div>
                <div style="color: #c7d2fe; font-size: 0.8rem; font-weight: 600; margin-top: 4px;">SQLite Storage</div>
                <div style="color: #64748b; font-size: 0.7rem;">WAL Mode</div>
            </div>
            <div style="color: #4f46e5; font-size: 1.2rem;">→</div>
            <div style="background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.3); border-radius: 12px; padding: 14px 20px; min-width: 140px;">
                <div style="font-size: 1.5rem;">📊</div>
                <div style="color: #c7d2fe; font-size: 0.8rem; font-weight: 600; margin-top: 4px;">Baseline Profiling</div>
                <div style="color: #64748b; font-size: 0.7rem;">Z-Score (μ, σ)</div>
            </div>
            <div style="color: #4f46e5; font-size: 1.2rem;">→</div>
            <div style="background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.3); border-radius: 12px; padding: 14px 20px; min-width: 140px;">
                <div style="font-size: 1.5rem;">🔍</div>
                <div style="color: #c7d2fe; font-size: 0.8rem; font-weight: 600; margin-top: 4px;">Detection Engine</div>
                <div style="color: #64748b; font-size: 0.7rem;">4 Modules</div>
            </div>
            <div style="color: #4f46e5; font-size: 1.2rem;">→</div>
            <div style="background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.3); border-radius: 12px; padding: 14px 20px; min-width: 140px;">
                <div style="font-size: 1.5rem;">🚨</div>
                <div style="color: #c7d2fe; font-size: 0.8rem; font-weight: 600; margin-top: 4px;">Alert Generation</div>
                <div style="color: #64748b; font-size: 0.7rem;">Risk Scoring</div>
            </div>
            <div style="color: #4f46e5; font-size: 1.2rem;">→</div>
            <div style="background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(139,92,246,0.2)); border: 1px solid rgba(139,92,246,0.4); border-radius: 12px; padding: 14px 20px; min-width: 140px;">
                <div style="font-size: 1.5rem;">📺</div>
                <div style="color: #c7d2fe; font-size: 0.8rem; font-weight: 600; margin-top: 4px;">Dashboard</div>
                <div style="color: #a78bfa; font-size: 0.7rem;">You are here</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── Raw Data Explorer ──
    st.markdown("#### Data Explorer")
    data_tabs = st.tabs(["📋 Alerts Table", "📊 Baselines Table", "📁 Raw Events"])
    
    with data_tabs[0]:
        st.dataframe(alerts_df, use_container_width=True, hide_index=True, height=300)
    with data_tabs[1]:
        st.dataframe(baselines_df, use_container_width=True, hide_index=True, height=300)
    with data_tabs[2]:
        if not events_df.empty:
            st.dataframe(events_df.head(500), use_container_width=True, hide_index=True, height=300)
        else:
            st.info("No event data loaded.")

