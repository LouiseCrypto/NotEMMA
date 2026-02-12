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

# Helper function to show the board in multiple places
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
    /* Force all labels and text to be dark navy */
    label, p, span, div { color: #1c3d5a !important; }
    /* Fix for invisible numbers in inputs */
    input { color: #1c3d5a !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'on_shift' not in st.session_state:
    st.session_state.on_shift = False

# --- VIEW 1: LANDING PAGE (Logged Out) ---
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
    
    # READ-ONLY BOARD FOR LANDING PAGE
    show_handover_board()

# --- VIEW 2: DASHBOARD (Logged In) ---
else:
    # Quick Stats
    conn = sqlite3.connect(DB_FILE)
    today = datetime.now().strftime("%Y-%m-%d")
    jobs_today = conn.execute("SELECT COUNT(*) FROM history WHERE timestamp LIKE ?", (f"{today}%",)).fetchone()[0]
    conn.close()
    
    st.metric("Jobs Completed (Site Today)", jobs_today)

    tab1, tab2, tab3 = st.tabs(["⚡ TASKS", "⏰ OVERTIME", "📢 HANDOVER"])

    with tab1:
        type_choice = st.radio("Priority", ["PPM", "Reactive"], horizontal=True)
        if type_choice == "PPM":
            tasks = ["DRUPS testing", "Flushing", "Fire Door Inspection", "Sprinkler testing"]
        else:
            tasks = ["Change light fitting", "Change lock", "Change flush plate"]
            
        selected_job = st.selectbox("Select Asset", tasks)
        
        # --- SPECIFIC JOB HISTORY ---
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
        ot_hours = st.number_input("Hours", min_value=0.0, step=0.5)
        ot_reason = st.text_input("Reason")
        if st.button("💾 SAVE"):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT INTO overtime (engineer, date, hours, reason) VALUES (?,?,?,?)",
                      (st.session_state.current_user, today, ot_hours, ot_reason))
            conn.commit()
            conn.close()
            st.balloons()

    with tab3:
        msg = st.text_area("Broadcast message")
        if st.button("📢 POST", use_container_width=True):
            if msg:
                conn = sqlite3.connect(DB_FILE)
                conn.execute("INSERT INTO handover (engineer, message, timestamp) VALUES (?,?,?)",
                          (st.session_state.current_user, msg, datetime.now().strftime("%H:%M | %d/%m")))
                conn.commit()
                conn.close()
                st.rerun()
        show_handover_board()

    with st.sidebar:
        st.title("⚙️ NotEMMA")
        st.write(f"User: {st.session_state.current_user}")
        if st.button("🚪 LOGOUT"):
            st.session_state.on_shift = False
            st.rerun()