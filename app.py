import streamlit as st
import sqlite3
import os
from datetime import datetime

# --- PERMANENT DATABASE PATH ---
# This points to the Render Disk we created
DB_FOLDER = "/opt/render/project/src/data"
DB_FILE = os.path.join(DB_FOLDER, "notemma.db")

# Create the folder if it doesn't exist (safety check)
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
st.set_page_config(page_title="NotEMMA", layout="centered")

# --- CUSTOM COLORS (Green/Red Buttons) ---
st.markdown("""
    <style>
    div.stButton > button:first-child { height: 4em; font-size: 20px !important; font-weight: bold; border-radius: 15px; }
    /* Success Button (Start) */
    div[data-testid="stBaseButton-secondary"] { background-color: #28a745; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏗️ NotEMMA Maintenance")

# --- LOGIN SECTION (On Main Page) ---
if 'on_shift' not in st.session_state:
    st.session_state.on_shift = False
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.on_shift:
    st.subheader("Engineer Sign-In")
    engineers = ["Select Name...", "Smiler", "Twig", "Gaz", "2 Hotty", "Iron Man", "Long hair", "Jackie Boy", "KP AP"]
    selected_user = st.selectbox("Choose your name:", engineers)
    
    pin = st.text_input("Enter PIN (1234):", type="password")
    
    if st.button("🟢 START SHIFT", use_container_width=True):
        if selected_user != "Select Name..." and pin == "1234":
            st.session_state.authenticated = True
            st.session_state.on_shift = True
            st.session_state.current_user = selected_user
            st.rerun()
        else:
            st.error("Please select a name and enter the correct PIN.")

# --- ON SHIFT VIEW ---
else:
    st.info(f"Logged in as: **{st.session_state.current_user}**")
    
    if st.button("🔴 FINISH SHIFT", use_container_width=True):
        st.session_state.on_shift = False
        st.session_state.authenticated = False
        st.rerun()

    st.divider()
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["PPMs", "Reactives", "Overtime", "Handover", "📞 Support"])

    with tab1:
        st.subheader("PPM Jobs")
        job = st.selectbox("Task", ["DRUPS testing", "Flushing", "Fire Door Inspection", "Sprinkler testing"])
        
        # --- JOB HISTORY VIEW ---
        st.markdown("### 📜 Previous Work History")
        conn = sqlite3.connect(DB_FILE)
        history = conn.execute("SELECT engineer, action, notes, timestamp FROM history WHERE job = ? ORDER BY id DESC LIMIT 3", (job,)).fetchall()
        if history:
            for h in history:
                st.write(f"🕒 **{h[3]}** | {h[0]}: *{h[1]}* - {h[2]}")
        else:
            st.write("No history found for this asset.")
        conn.close()
        st.divider()

        action = st.radio("Action", ["Visual inspection", "Routine Maintenance", "Repair/Replace part"])
        notes = st.text_area("Notes", key="ppm_notes")
        if st.button("Submit PPM Log"):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT INTO history (engineer, type, job, action, notes, timestamp) VALUES (?,?,?,?,?,?)",
                      (st.session_state.current_user, "PPM", job, action, notes, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            st.success("PPM Logged!")

    with tab2:
        st.subheader("Reactive Jobs")
        r_job = st.selectbox("Task", ["Change light fitting", "Change lock", "Change flush plate"])
        
        # --- JOB HISTORY VIEW ---
        st.markdown("### 📜 Previous Work History")
        conn = sqlite3.connect(DB_FILE)
        r_history = conn.execute("SELECT engineer, action, notes, timestamp FROM history WHERE job = ? ORDER BY id DESC LIMIT 3", (r_job,)).fetchall()
        if r_history:
            for rh in r_history:
                st.write(f"🕒 **{rh[3]}** | {rh[0]}: *{rh[1]}* - {rh[2]}")
        else:
            st.write("No history found for this asset.")
        conn.close()
        st.divider()

        r_action = st.radio("What did you do?", ["Visual inspection", "Routine Maintenance", "Repair/Replace part"])
        r_notes = st.text_area("Details", key="react_notes")
        if st.button("Submit Reactive"):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT INTO history (engineer, type, job, action, notes, timestamp) VALUES (?,?,?,?,?,?)",
                      (st.session_state.current_user, "Reactive", r_job, r_action, r_notes, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            st.success("Reactive Job Logged!")

    with tab3:
        st.subheader("Overtime Log")
        ot_date = st.date_input("Date")
        ot_hours = st.number_input("Hours", min_value=0.0, step=0.5)
        ot_reason = st.text_input("Reason")
        if st.button("Save Overtime"):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT INTO overtime (engineer, date, hours, reason) VALUES (?,?,?,?)",
                      (st.session_state.current_user, str(ot_date), ot_hours, ot_reason))
            conn.commit()
            conn.close()
            st.success("Saved!")

    with tab4:
        st.subheader("Post Handover")
        msg = st.text_area("Message for next shift")
        if st.button("Add to Board"):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT INTO handover (engineer, message, timestamp) VALUES (?,?,?)",
                      (st.session_state.current_user, msg, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            st.rerun()

    with tab5:
        st.subheader("Support Contacts")
        st.write("📞 **Helpdesk:** 0123 456 789")
        st.write("📞 **TOMS:** 0987 654 321")
        st.write("🆘 **Emergency:** Extension 999")

# --- ALWAYS VISIBLE HANDOVER BOARD (At Bottom) ---
st.divider()
st.subheader("📋 Shift Handover Board (Read-only)")
conn = sqlite3.connect(DB_FILE)
logs = conn.execute("SELECT engineer, message, timestamp FROM handover ORDER BY id DESC LIMIT 5").fetchall()
if logs:
    for l in logs:
        st.warning(f"**{l[0]}** ({l[2]}): {l[1]}")
else:
    st.write("No active handover notes.")
conn.close()