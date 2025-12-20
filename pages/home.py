import streamlit as st
from supabase_client import supabase
from datetime import datetime
from utils.model import detect_face_and_predict
from PIL import Image
import numpy as np
import pytz

st.set_page_config(page_title="Veritas | Home", layout="wide")

st.markdown("""
    <style>
    div.block-container { max-width: 1300px; padding-top: 5rem; }
    div[data-testid="stHorizontalBlock"] { gap: 2rem; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #0080ff; }
    </style>
    """, unsafe_allow_html=True)

# Login Check
user = st.session_state.get("user")
if not user:
    st.warning("You must be logged in.")
    st.stop()

header_col, logout_col = st.columns([8, 1])
with header_col:
    st.title("Veritas – Attendance System")
with logout_col:
    if st.button("Logout"):
        from utils.auth import logout
        logout()
        st.switch_page("app.py")

# Main Layout
col1, col2 = st.columns([2, 1])

with col1:
    image = st.camera_input("Attendance Camera", label_visibility="collapsed")

with col2:
    st.markdown("### 📊 System Status")
    
    # Time logic
    wib = pytz.timezone("Asia/Jakarta")
    now = datetime.now(wib)
    
    st.metric("Current Time", now.strftime("%H:%M:%S"))
    st.metric("Class", "A0707")
    st.metric("Model Status", "🧠 Loaded & Active")
    st.metric("Database", "🟢 Connected")

# Procesing Logic
if image:
    img = Image.open(image).convert("RGB")
    frame = np.array(img)

    # Process Detection
    name, _ = detect_face_and_predict(frame)

    if name:
        timestamp = datetime.now(wib).strftime("[%Y-%m-%d] %H:%M:%S")

        try:
            supabase.table("attendance_log").insert({
                "timestamp": timestamp,
                "person_detected": name
            }).execute()

            st.success(f"✅ Attendance recorded for **{name}**")

        except Exception as e:
            st.error(f"Failed to log attendance: {e}")
    else:
        st.warning("⚠️ No face detected. Please align your face and try again.")

# Attendance Log
st.markdown("---")
st.markdown("### Attendance Log (Latest 20 Records")

try:
    logs = supabase.table("attendance_log") \
        .select("person_detected,timestamp") \
        .order("timestamp", desc=True) \
        .limit(10).execute().data

    # Displaying Logs
    for log in logs:
        st.write(f"**{log['timestamp']}** — {log['person_detected']}")
except Exception as e:
    st.error("Could not load logs from database.")