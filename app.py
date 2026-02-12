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

# --- CUSTOM CSS FOR THE 'WOW' FACTOR ---
st.markdown("""
    <style>
    /* Force dark text globally */
    html, body, [data-testid="stWidgetLabel"], p, li {
        color: #1c3d5a !important;
    }
    
    /* Clean up Tabs - Remove the grey boxes */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent !important;
        border: none !important;
        font-weight: 400;
    }
    .stTabs [aria-selected="true"] {
        font-weight: bold !important;
        color: #ff4b4b !important; /* Matches the red underline */
    }

    /* Fix Overtime Input visibility */
    input[type="number"] {
        color: #1c3d5a !important;
        font-weight: bold;
    }

    /* Handover Card Style */
    .handover-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 10px;
        color: #1c3d5a;
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
    st.subheader("Engineer Sign-In")
    
    engineers = ["Select Name...", "Smiler", "Twig", "Gaz", "2 Hotty", "Iron Man", "Long hair", "Jackie Boy", "KP AP"]
    selected_user = st.selectbox("Identify yourself:", engineers)
    pin = st.text_input("PIN", type="password")
    
    if st.button("🚀 START SHIFT", use_container_width=True, type="primary"):
        if selected_user != "Select Name..." and pin == "1234":
            st.session_state.on_shift = True
            st.session_state.current_user = selected_user
            st.rerun()
        else:
            st.error("Invalid Login.")

# --- VIEW 2: DASHBOARD ---
else:
    with st.sidebar:
        st.title("🛠️ NotEMMA")
        st.write(f"Engineer: **{st.session_state.current_user}**")
        if st.button("🚪 Logout"):
            st.session_state.on_shift = False
            st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["Tasks", "Overtime", "Handover", "History"])

    with tab1:
        st.subheader("Log Work")
        type_choice = st.radio("Type", ["PPM", "Reactive"], horizontal=True)
        
        # --- SMART DROPDOWN LOGIC ---
        if type_choice == "PPM":
            tasks = ["DRUPS testing", "Flushing", "Fire Door Inspection", "Sprinkler testing"]
        else:
            tasks = ["Change light fitting", "Change lock", "Change flush plate"]
            
        task = st.selectbox("Select Asset/Task", tasks)
        action = st.radio("Action", ["Visual inspection", "Routine Maintenance", "Repair/Replace"])
        notes = st.text_area("Detailed Findings")
        
        if st.button("✅ Submit Work Log", use_container_width=True):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT INTO history (engineer, type, job, action, notes, timestamp) VALUES (?,?,?,?,?,?)",
                      (st.session_state.current_user, type_choice, task, action, notes, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            st.success(f"{type_choice} Recorded!")

    with tab2:
        st.subheader("Extra Hours")
        # Added a container to make sure input is visible
        ot_hours = st.number_input("Hours Worked", min_value=0.0, step=0.5, format="%.1f")
        ot_reason = st.text_input("Reason for OT (e.g. Call-out)")
        
        if st.button("💾 Save Overtime"):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT INTO overtime (engineer, date, hours, reason) VALUES (?,?,?,?)",
                      (st.session_state.current_user, str(datetime.now().date()), ot_hours, ot_reason))
            conn.commit()
            conn.close()
            st.balloons()
            st.success("Hours added to record.")

    with tab3:
        st.subheader("Shift Handover Board")
        msg = st.text_area("Update for the next engineer")
        if st.button("📢 Post to Board", use_container_width=True):
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
            st.markdown(f"""<div class="handover-card"><div style="font-weight:bold; color:#28a745;">👷 {l[0]} | {l[2]}</div>{l[1]}</div>""", unsafe_allow_html=True)

    with tab4:
        st.subheader("Recent Activity")
        conn = sqlite3.connect(DB_FILE)
        # Showing a cleaner history
        history = conn.execute("SELECT type, job, timestamp FROM history ORDER BY id DESC LIMIT 10").fetchall()
        conn.close()
        if history:
            st.table(history)
        else:
            st.info("No work logged in this session yet.")