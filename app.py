import streamlit as st
import sqlite3
import os
import pandas as pd
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

def show_handover_board():
    st.divider()
    st.subheader("📋 Live Handover Board")
    conn = sqlite3.connect(DB_FILE)
    logs = conn.execute("SELECT engineer, message, timestamp FROM handover ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()
    
    if logs:
        for l in logs:
            st.markdown(f"""
            <div style="background: white; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 10px;">
                <div style="color: #666; font-size: 0.8em;">{l[2]}</div>
                <div style="color: #ff4b4b; font-weight: bold; font-size: 1.1em;">👷 {l[0]}</div>
                <div style="color: #1c3d5a; margin-top: 5px; font-size: 1em;">{l[1]}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No active handover notes.")

init_db()

# --- APP CONFIG ---
st.set_page_config(page_title="NotEMMA", page_icon="🏗️", layout="centered")

# --- GLOBAL STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    label, p, span, div { color: #1c3d5a !important; }
    input { color: #1c3d5a !important; font-weight: bold !important; }
    /* Metric styling */
    div[data-testid="stMetricValue"] { color: #ff4b4b !important; font-size: 32px; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'on_shift' not in st.session_state:
    st.session_state.on_shift = False

# --- VIEW 1: LANDING PAGE ---
if not st.session_state.on_shift:
    st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&q=80&w=800", use_container_width=True)
    st.title("🏗️ NotEMMA")
    
    with st.expander("🔐 Engineer Login", expanded=True):
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
    
    show_handover_board()

# --- VIEW 2: DASHBOARD ---
else:
    # --- DATA CALCULATIONS FOR TOP METRICS ---
    conn = sqlite3.connect(DB_FILE)
    today = datetime.now().strftime("%Y-%m-%d")
    current_month = datetime.now().strftime("%Y-%m")
    
    jobs_today = conn.execute("SELECT COUNT(*) FROM history WHERE timestamp LIKE ?", (f"{today}%",)).fetchone()[0]
    
    # Calculate Monthly OT for CURRENT user only
    ot_query = conn.execute("SELECT SUM(hours) FROM overtime WHERE engineer = ? AND date LIKE ?", 
                            (st.session_state.current_user, f"{current_month}%")).fetchone()[0]
    monthly_ot = ot_query if ot_query else 0.0
    conn.close()
    
    # --- TOP METRICS ---
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.metric("Jobs (Site Today)", jobs_today)
    with m_col2:
        st.metric("Your OT (This Month)", f"{monthly_ot} hrs")

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚡ TASKS", "⏰ OVERTIME", "📢 HANDOVER", "📜 HISTORY", "📞 SUPPORT"])

    with tab1:
        type_choice = st.radio("Priority", ["PPM", "Reactive"], horizontal=True)
        tasks = ["DRUPS testing", "Flushing", "Fire Door Inspection", "Sprinkler testing"] if type_choice == "PPM" else ["Change light fitting", "Change lock", "Change flush plate"]
        selected_job = st.selectbox("Select Asset", tasks)
        
        # Specific Job History
        st.markdown(f"#### 📜 History for: {selected_job}")
        conn = sqlite3.connect(DB_FILE)
        job_history = conn.execute("SELECT engineer, action, notes, timestamp FROM history WHERE job = ? ORDER BY id DESC LIMIT 3", (selected_job,)).fetchall()
        conn.close()
        if job_history:
            for jh in job_history:
                st.markdown(f"**{jh[3]}** - {jh[0]}: *{jh[1]}* <br> {jh[2]}", unsafe_allow_html=True)
        else:
            st.caption("No previous history for this asset.")
        
        st.divider()
        action = st.radio("Action", ["Inspection", "Routine", "Repair"], horizontal=True)
        notes = st.text_area("Notes")
        if st.button("✅ FINALIZE LOG", use_container_width=True):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT INTO history (engineer, type, job, action, notes, timestamp) VALUES (?,?,?,?,?,?)",
                      (st.session_state.current_user, type_choice, selected_job, action, notes, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            st.success("Logged!")
            st.rerun()

    with tab2:
        st.subheader("Log Overtime")
        ot_hours = st.number_input("Hours", min_value=0.0, step=0.5)
        ot_reason = st.text_input("Reason")
        if st.button("💾 SAVE"):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT INTO overtime (engineer, date, hours, reason) VALUES (?,?,?,?)",
                      (st.session_state.current_user, today, ot_hours, ot_reason))
            conn.commit()
            conn.close()
            st.balloons()
            st.rerun()

    with tab3:
        st.subheader("Handover Update")
        msg = st.text_area("Message for next shift")
        if st.button("📢 POST", use_container_width=True):
            if msg:
                conn = sqlite3.connect(DB_FILE)
                conn.execute("INSERT INTO handover (engineer, message, timestamp) VALUES (?,?,?)",
                          (st.session_state.current_user, msg, datetime.now().strftime("%H:%M | %d/%m")))
                conn.commit()
                conn.close()
                st.rerun()
        show_handover_board()

    with tab4:
        st.subheader("Global Site Log (Full History)")
        conn = sqlite3.connect(DB_FILE)
        # Pulling the full history table
        df = pd.read_sql_query("SELECT timestamp, engineer, type, job, action, notes FROM history ORDER BY id DESC", conn)
        conn.close()
        # Displaying as a professional Excel-like dataframe
        st.dataframe(df, use_container_width=True)

    with tab5:
        st.subheader("📞 Support Contacts")
        c1, c2 = st.columns(2)
        with c1:
            st.info("**Helpdesk**\n\n0121 555 1234")
            st.info("**Site Supervisor**\n\n07700 900 123")
        with c2:
            st.info("**TOMS Support**\n\n0800 123 4567")
            st.info("**Security/Fire**\n\nExt 999")

    with st.sidebar:
        st.title("⚙️ NotEMMA")
        st.write(f"Logged in: **{st.session_state.current_user}**")
        if st.button("🚪 LOGOUT"):
            st.session_state.on_shift = False
            st.rerun()