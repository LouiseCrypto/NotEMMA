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

# --- APP CONFIG & THEME ---
st.set_page_config(page_title="NotEMMA | Maintenance", page_icon="🏗️", layout="centered")

# --- ADVANCED STYLING (The "Fancy" Part) ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #f8f9fa; }
    
    /* Custom Card Style for Handover */
    .handover-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    
    /* Status Headers */
    .engineer-tag {
        color: #1c3d5a;
        font-weight: bold;
        font-size: 0.9em;
        text-transform: uppercase;
    }
    
    /* Make buttons pop */
    div.stButton > button {
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&q=80&w=800", use_container_width=True)
st.title("🏗️ NotEMMA")
st.caption("Site Maintenance & Engineering Management")

# --- SESSION STATE ---
if 'on_shift' not in st.session_state:
    st.session_state.on_shift = False

# --- LOGIN SECTION ---
if not st.session_state.on_shift:
    with st.container():
        st.subheader("🔐 Engineer Access")
        engineers = ["Select Name...", "Smiler", "Twig", "Gaz", "2 Hotty", "Iron Man", "Long hair", "Jackie Boy", "KP AP"]
        
        col1, col2 = st.columns(2)
        with col1:
            selected_user = st.selectbox("Identity", engineers)
        with col2:
            pin = st.text_input("Security PIN", type="password")
        
        if st.button("🚀 START SHIFT", use_container_width=True, type="primary"):
            if selected_user != "Select Name..." and pin == "1234":
                st.session_state.on_shift = True
                st.session_state.current_user = selected_user
                st.rerun()
            else:
                st.error("Access Denied. Check credentials.")

# --- MAIN APP VIEW ---
else:
    # Sidebar for logout and info
    with st.sidebar:
        st.header("👤 Profile")
        st.write(f"Logged in: **{st.session_state.current_user}**")
        st.write(f"Date: {datetime.now().strftime('%d %b %Y')}")
        if st.button("🚪 Finish Shift", use_container_width=True):
            st.session_state.on_shift = False
            st.rerun()
        
        st.divider()
        st.subheader("📞 Quick Support")
        st.caption("Helpdesk: 0123 456 789")
        st.caption("Emergency: Ext 999")

    # Main Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Tasks", "⏰ Overtime", "📝 Handover Board", "📊 History"])

    with tab1:
        st.subheader("Log Work")
        type_choice = st.radio("Job Type", ["PPM", "Reactive"], horizontal=True)
        
        if type_choice == "PPM":
            task = st.selectbox("Task", ["DRUPS testing", "Flushing", "Fire Door Inspection", "Sprinkler testing"])
        else:
            task = st.selectbox("Task", ["Change light fitting", "Change lock", "Change flush plate"])
            
        action = st.radio("Action Taken", ["Visual inspection", "Routine Maintenance", "Repair/Replace part"])
        notes = st.text_area("Findings & Notes")
        
        if st.button("✅ Submit Work Log", use_container_width=True):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT INTO history (engineer, type, job, action, notes, timestamp) VALUES (?,?,?,?,?,?)",
                      (st.session_state.current_user, type_choice, task, action, notes, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            st.success("Work logged successfully!")

    with tab2:
        st.subheader("Extra Hours")
        c1, c2 = st.columns(2)
        with c1:
            ot_date = st.date_input("Date of OT")
        with c2:
            ot_hours = st.number_input("Hours", min_value=0.0, step=0.5)
        ot_reason = st.text_input("Reason for Overtime")
        if st.button("Save Overtime"):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT INTO overtime (engineer, date, hours, reason) VALUES (?,?,?,?)",
                      (st.session_state.current_user, str(ot_date), ot_hours, ot_reason))
            conn.commit()
            conn.close()
            st.balloon()
            st.success("Overtime recorded!")

    with tab3:
        st.subheader("Post Shift Message")
        msg = st.text_area("What does the next shift need to know?")
        if st.button("📢 Broadcast to Board", use_container_width=True):
            if msg:
                conn = sqlite3.connect(DB_FILE)
                conn.execute("INSERT INTO handover (engineer, message, timestamp) VALUES (?,?,?)",
                          (st.session_state.current_user, msg, datetime.now().strftime("%H:%M | %d/%m")))
                conn.commit()
                conn.close()
                st.rerun()

        st.divider()
        st.subheader("Live Handover Board")
        conn = sqlite3.connect(DB_FILE)
        logs = conn.execute("SELECT engineer, message, timestamp FROM handover ORDER BY id DESC LIMIT 5").fetchall()
        conn.close()
        
        if logs:
            for l in logs:
                st.markdown(f"""
                <div class="handover-card">
                    <div class="engineer-tag">👷 {l[0]} | {l[2]}</div>
                    <div style="font-size: 1.1em; padding-top: 10px;">{l[1]}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("The board is currently clear.")

    with tab4:
        st.subheader("Recent Activity")
        conn = sqlite3.connect(DB_FILE)
        history = conn.execute("SELECT engineer, job, action, timestamp FROM history ORDER BY id DESC LIMIT 10").fetchall()
        conn.close()
        if history:
            st.table(history) # Nice clean table view
        else:
            st.write("No activity recorded yet.")