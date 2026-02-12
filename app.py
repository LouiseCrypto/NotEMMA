import streamlit as st
import sqlite3
import os
from datetime import datetime

# --- PERMANENT DATABASE PATH ---
DB_FOLDER = "/opt/render/project/src/data"
DB_FILE = os.path.join(DB_FOLDER, "notemma.db")

if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY, engineer TEXT, type TEXT, job TEXT, action TEXT, notes TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS overtime 
                 (id INTEGER PRIMARY KEY, engineer TEXT, date TEXT, hours REAL, reason TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS handover 
                 (id INTEGER PRIMARY KEY, engineer TEXT, message TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- APP CONFIG ---
st.set_page_config(page_title="NotEMMA", page_icon="🏗️", layout="centered")

# --- PREMIUM STYLING ---
st.markdown("""
    <style>
    /* Global Background & Text */
    .stApp { background-color: #f0f2f6; }
    h1, h2, h3, p, span, label { color: #1c3d5a !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Metric Card Styling */
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; color: #ff4b4b; }
    div[data-testid="metric-container"] {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    /* Tab Customization */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff !important;
        border-radius: 8px 8px 0px 0px !important;
        padding: 10px 20px !important;
        border: 1px solid #e1e4e8 !important;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 3px solid #ff4b4b !important;
        color: #ff4b4b !important;
    }

    /* Handover Board Card */
    .handover-card {
        background: linear-gradient(135deg, #ffffff 0%, #f9f9f9 100%);
        padding: 20px;
        border-radius: 15px;
        border-left: 6px solid #28a745;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'on_shift' not in st.session_state:
    st.session_state.on_shift = False

# --- VIEW 1: LOGIN PAGE ---
if not st.session_state.on_shift:
    st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&q=80&w=800", use_container_width=True)
    st.title("🏗️ NotEMMA")
    st.markdown("### *Site Engineering Intelligence*")
    
    with st.expander("🔑 Secure Login", expanded=True):
        engineers = ["Select Name...", "Smiler", "Twig", "Gaz", "2 Hotty", "Iron Man", "Long hair", "Jackie Boy", "KP AP"]
        selected_user = st.selectbox("Identify yourself:", engineers)
        pin = st.text_input("PIN", type="password")
        
        if st.button("🚀 START SHIFT", use_container_width=True, type="primary"):
            if selected_user != "Select Name..." and pin == "1234":
                st.session_state.on_shift = True
                st.session_state.current_user = selected_user
                st.rerun()
            else:
                st.error("Invalid Credentials.")

# --- VIEW 2: DASHBOARD ---
else:
    # --- TOP BAR STATS (The "Wow" Factor) ---
    conn = sqlite3.connect(DB_FILE)
    today_date = datetime.now().strftime("%Y-%m-%d")
    jobs_today = conn.execute("SELECT COUNT(*) FROM history WHERE timestamp LIKE ?", (f"{today_date}%",)).fetchone()[0]
    total_ot = conn.execute("SELECT SUM(hours) FROM overtime WHERE engineer = ?", (st.session_state.current_user,)).fetchone()[0] or 0
    conn.close()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Jobs Completed (Site)", jobs_today)
    with col2:
        st.metric("Your Total OT (Hrs)", f"{total_ot:.1f}")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["⚡ TASKS", "🕒 OVERTIME", "📝 HANDOVER", "📜 LOGS"])

    with tab1:
        type_choice = st.radio("Choose Priority", ["PPM", "Reactive"], horizontal=True)
        
        if type_choice == "PPM":
            tasks = ["DRUPS testing", "Flushing", "Fire Door Inspection", "Sprinkler testing"]
            st.info("💡 Scheduled Maintenance Mode")
        else:
            tasks = ["Change light fitting", "Change lock", "Change flush plate"]
            st.warning("⚠️ Reactive Repair Mode")
            
        task = st.selectbox("Select Asset", tasks)
        action = st.segmented_control("Action taken:", ["Inspection", "Routine", "Repair"], default="Inspection")
        notes = st.text_area("Engineer Notes", placeholder="Detail what was found and fixed...")
        
        if st.button("✅ FINALIZE LOG", use_container_width=True):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT INTO history (engineer, type, job, action, notes, timestamp) VALUES (?,?,?,?,?,?)",
                      (st.session_state.current_user, type_choice, task, action, notes, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            st.success("Log submitted to cloud.")

    with tab2:
        st.subheader("Extra Hours Tracker")
        ot_hours = st.number_input("Hours", min_value=0.0, step=0.5)
        ot_reason = st.text_input("Reason / Call-out Reference")
        if st.button("💾 SAVE HOURS"):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT INTO overtime (engineer, date, hours, reason) VALUES (?,?,?,?)",
                      (st.session_state.current_user, today_date, ot_hours, ot_reason))
            conn.commit()
            conn.close()
            st.balloons()

    with tab3:
        st.subheader("Digital Handover Board")
        msg = st.text_area("Broadcast message to the team", placeholder="E.g. Pump 2 is isolated...")
        if st.button("📢 POST TO BOARD", use_container_width=True):
            if msg:
                conn = sqlite3.connect(DB_FILE)
                conn.execute("INSERT INTO handover (engineer, message, timestamp) VALUES (?,?,?)",
                          (st.session_state.current_user, msg, datetime.now().strftime("%H:%M | %d/%m")))
                conn.commit()
                conn.close()
                st.rerun()

        st.divider()
        conn = sqlite3.connect(DB_FILE)
        logs = conn.execute("SELECT engineer, message, timestamp FROM handover ORDER BY id DESC LIMIT 5").fetchall()
        conn.close()
        for l in logs:
            st.markdown(f"""
            <div class="handover-card">
                <div style="font-size:0.8em; color:#666;">{l[2]}</div>
                <div style="font-weight:bold; color:#ff4b4b; font-size:1.1em;">👷 {l[0]}</div>
                <div style="margin-top:10px; font-size:1.05em;">{l[1]}</div>
            </div>
            """, unsafe_allow_html=True)

    with tab4:
        st.subheader("Site Activity Log")
        conn = sqlite3.connect(DB_FILE)
        history = conn.execute("SELECT engineer, type, job, timestamp FROM history ORDER BY id DESC LIMIT 15").fetchall()
        conn.close()
        st.dataframe(history, use_container_width=True) # Makes it look more like a pro table

    # Sidebar for logout
    with st.sidebar:
        st.title("⚙️ NotEMMA")
        st.write(f"Logged in: **{st.session_state.current_user}**")
        st.divider()
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state.on_shift = False
            st.rerun()