import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import config

# Sayfa ayarlarını dark mode ve geniş layout yapıyoruz
st.set_page_config(page_title="SentinelRemote AI Dashboard", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS (Hacker/Cybersecurity Teması) ---
# Öğrenciler genelde havalı dursun diye böyle neon CSS'ler ekler
st.markdown("""
<style>
    /* Ana arkaplan ve fontlar */
    .stApp {
        background-color: #0e1117;
        color: #c9d1d9;
    }
    
    /* Basliklar icin glow efekti */
    h1, h2, h3 {
        color: #58a6ff !important;
        text-shadow: 0 0 10px rgba(88, 166, 255, 0.3);
        font-family: 'Courier New', Courier, monospace;
    }
    
    /* Metric kartlari icin Cyberpunk / Glassmorphism efekti */
    div[data-testid="metric-container"] {
        background: rgba(30, 30, 40, 0.6);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s ease-in-out, box-shadow 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 15px rgba(88, 166, 255, 0.4);
        border-color: #58a6ff;
    }
    
    /* Metric yazilari */
    div[data-testid="metric-container"] > div > div > div {
        color: #8b949e !important;
        font-weight: 600;
        font-size: 1rem;
    }
    div[data-testid="metric-container"] > div > div > div:nth-child(2) {
        color: #ffffff !important;
        font-size: 2rem;
        font-weight: bold;
    }
    
    /* Sidebar ozellestirmeleri */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* Tablo kapsayicisi */
    .dataframe-container {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #30363d;
    }
</style>
""", unsafe_allow_html=True)


# function to load data from database
@st.cache_data(ttl=60)
def load_data():
    conn = sqlite3.connect(config.DB_PATH)
    
    try:
        alerts = pd.read_sql("SELECT * FROM " + config.ALERT_TABLE, conn)
        baselines = pd.read_sql("SELECT * FROM " + config.BASELINE_TABLE, conn)
        events = pd.read_sql("SELECT * FROM security_events", conn)
        
        # convert string dates to pandas datetime
        if not alerts.empty:
            alerts['timestamp'] = pd.to_datetime(alerts['timestamp'])
        if not events.empty:
            events['timestamp'] = pd.to_datetime(events['timestamp'])
    except Exception as e:
        alerts = pd.DataFrame()
        baselines = pd.DataFrame()
        events = pd.DataFrame()
        
    conn.close()
    return alerts, baselines, events

alerts_df, baselines_df, events_df = load_data()

# --- HEADER ---
col_logo, col_title = st.columns([1, 10])
with col_title:
    st.title("🛡️ SentinelRemote AI - Threat Detection Engine")
    st.markdown("*Advanced Insider Threat & Shadow AI Monitoring System*")

if alerts_df.empty or baselines_df.empty:
    st.warning("⚠️ No analysis results found in the database. Please run `python run_detection.py` first.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.markdown("## 📡 Control Panel")
st.sidebar.markdown("Filter incoming telemetry data:")

all_users = ["All"] + sorted(list(baselines_df['username'].unique()))
selected_user = st.sidebar.selectbox("👤 Select Target User", all_users)

risk_levels = ["All"] + list(alerts_df['risk_level'].unique())
selected_risk = st.sidebar.selectbox("⚠️ Risk Level", risk_levels)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛠️ System Status")
st.sidebar.success("Detection Engine: ONLINE")
st.sidebar.success("Database: CONNECTED")


# Filter data based on sidebar selections
f_alerts = alerts_df.copy()
f_events = events_df.copy()
f_base = baselines_df.copy()

if selected_user != "All":
    f_alerts = f_alerts[f_alerts['username'] == selected_user]
    f_events = f_events[f_events['username'] == selected_user]
    f_base = f_base[f_base['username'] == selected_user]

if selected_risk != "All":
    f_alerts = f_alerts[f_alerts['risk_level'] == selected_risk]


# --- TOP METRICS ---
st.markdown("### 📊 Network Telemetry Summary")
col1, col2, col3, col4, col5 = st.columns(5)

critical_count = len(alerts_df[alerts_df['risk_level'] == 'CRITICAL'])
review_count = len(alerts_df[alerts_df['risk_level'] == 'REVIEW'])
normal_count = len(alerts_df[alerts_df['risk_level'] == 'NORMAL'])
shadow_ai_count = len(alerts_df[alerts_df['category'] == 'SHADOW_AI'])

col1.metric("👥 Active Identities", len(baselines_df))
col2.metric("📝 Total Logs Analyzed", f"{events_df.shape[0]:,}")
col3.metric("🔴 CRITICAL Alerts", critical_count, delta="High Risk", delta_color="inverse")
col4.metric("🟡 REVIEW Required", review_count, delta="Moderate", delta_color="off")
col5.metric("🤖 SHADOW AI Hits", shadow_ai_count, delta="Policy Violation", delta_color="inverse")

st.markdown("<br>", unsafe_allow_html=True)


# --- MAIN LAYOUT (ROW 1) ---
row1_col1, row1_col2 = st.columns([1.5, 1])

with row1_col1:
    st.markdown("### 🚨 Threat Intelligence Alerts")
    if not f_alerts.empty:
        # Tabloyu daha şık göstermek için dataframe ayarları
        display_table = f_alerts[['timestamp', 'username', 'risk_level', 'category', 'reason']].copy()
        
        # Risk seviyesine gore emoji ekleyelim daha iyi dursun
        def add_emoji(val):
            if val == 'CRITICAL': return '🔴 CRITICAL'
            elif val == 'REVIEW': return '🟡 REVIEW'
            else: return '🟢 NORMAL'
            
        display_table['risk_level'] = display_table['risk_level'].apply(add_emoji)
        
        # Sort by timestamp descending
        display_table = display_table.sort_values(by='timestamp', ascending=False)
        
        st.dataframe(
            display_table,
            use_container_width=True,
            hide_index=True,
            height=350
        )
    else:
        st.success("✅ No threats detected for the selected filters.")

with row1_col2:
    st.markdown("### 📈 Z-Score Anomaly Profiles")
    if selected_user == "All":
        # Grouped bar chart with dark theme
        fig = px.bar(
            f_base, x='username', y=['volume_zscore', 'file_ops_zscore', 'delete_zscore'],
            barmode='group',
            labels={'value': 'Standard Deviation (Z)', 'variable': 'Metric Type', 'username': 'User'},
            color_discrete_sequence=['#58a6ff', '#f39c12', '#e74c3c'],
            template="plotly_dark"
        )
        fig.add_hline(y=3.0, line_dash="dash", line_color="#ff4b4b", annotation_text="Critical Threshold")
        fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    else:
        z_cols = ['volume_zscore', 'file_ops_zscore', 'delete_zscore']
        vals = f_base[z_cols].iloc[0].values
        fig = px.bar(
            x=['General Volume', 'File Operations', 'Deletions'], y=vals,
            labels={'x': 'Activity Category', 'y': 'Z-Score'},
            color=vals, color_continuous_scale=["#2ecc71", "#f39c12", "#e74c3c"],
            range_color=[0, 3.5],
            template="plotly_dark"
        )
        fig.add_hline(y=3.0, line_dash="dash", line_color="#ff4b4b", annotation_text="Critical Threshold")
        fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)


st.markdown("<br><hr>", unsafe_allow_html=True)

# --- MAIN LAYOUT (ROW 2) ---
st.markdown("### ⏱️ Timeline & Behavioral Pattern Analysis")

if not f_events.empty:
    col_chart1, col_chart2 = st.columns([1, 1])
    
    with col_chart1:
        # Time of day distribution
        f_events['hour'] = f_events['timestamp'].dt.hour
        hourly = f_events.groupby(['hour', 'action']).size().reset_index(name='count')
        
        fig_hour = px.bar(
            hourly, x="hour", y="count", color="action", barmode="stack",
            labels={'hour': 'Hour of Day (0-23)', 'count': 'Total Operations', 'action': 'Action Type'},
            color_discrete_map={"LOGIN": "#2ecc71", "LOGOUT": "#95a5a6", "READ": "#58a6ff", "WRITE": "#f39c12", "DELETE": "#e74c3c", "WEB_VISIT": "#9b59b6", "EMAIL": "#00ced1"},
            template="plotly_dark"
        )
        # highlight the night shift
        fig_hour.add_vrect(x0=-0.5, x1=6.5, fillcolor="red", opacity=0.15, layer="below", line_width=0, annotation_text="Night (High Risk)")
        fig_hour.update_layout(margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_hour, use_container_width=True)
        
    with col_chart2:
        # Detailed scatter plot
        fig_scatter = px.scatter(
            f_events, x="timestamp", y="action", color="username",
            hover_data=["details"], title="Event Sequence Flow",
            color_discrete_sequence=px.colors.qualitative.Set2,
            template="plotly_dark"
        )
        fig_scatter.update_traces(marker=dict(size=8, opacity=0.7, line=dict(width=1, color='DarkSlateGrey')))
        fig_scatter.update_layout(margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_scatter, use_container_width=True)

else:
    st.info("No behavioral (event) records found for these filters.")

# Footer
st.markdown("<br><div style='text-align: center; color: #8b949e; font-size: 0.8rem;'>SentinelRemote AI - Graduation Project Dashboard</div>", unsafe_allow_html=True)
