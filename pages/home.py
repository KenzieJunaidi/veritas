import streamlit as st
from supabase_client import supabase
from datetime import datetime
import cv2
import time
import numpy as np
from utils.model import detect_face_and_predict
from PIL import Image
import pytz

st.set_page_config(page_title="Veritas | Home", layout="wide")

# CSS Injection (Fix Gap between Coloumns)
st.markdown(
    """
    <style>
    div.block-container {
        max-width: 1300px;
    }

    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
    }
    /* Custom style to make the clock metric stand out a bit */
    [data-testid="stMetricValue"] {
        font-size: 2rem; /* Larger font for time */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Login Check
user = st.session_state.get("user")
if not user:
    st.warning("You must be logged in to use the Home page. Please login first.")
    st.stop()

# Session State
if "current_name" not in st.session_state:
    st.session_state.current_name = None

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "local_log" not in st.session_state:
    st.session_state.local_log = []

DETECTION_DURATION = 1.5  # Time needed to Confirm Attendance

# Logout Button
top_left, top_right = st.columns([8, 1])

with top_right:
    if st.button("Logout"):
        from utils.auth import logout
        logout()
        st.rerun()

# Main Layout
col1, col2 = st.columns([2, 1])

SUCCESS_MESSAGE_PLACEHOLDER = st.empty()

# Camera Div
with col1:
    st.markdown("## Live Camera Feed")
    FRAME_WINDOW = st.image([])

    cap = cv2.VideoCapture(0)
    camera_status = "🔴 Not Connected"

    if cap.isOpened():
        camera_status = "🟢 Active (ID: 10)"
    else:
        camera_status = "🔴 Failed to Load"

# Status Div
with col2:
    st.markdown("## System Status (Demo)")

    # 1. Clock Placeholder - Added here
    CLOCK_PLACEHOLDER = st.empty() 

    class_name = "A0707"
    model_status = "🧠 Model Loaded"
    connection_status = camera_status
    demo_fps = 30.00

    st.metric("Class", class_name)
    st.metric("Camera Status", connection_status)
    st.metric("Model Status", model_status)
    st.metric("FPS", demo_fps)

# Attendance Log
st.markdown("---")
st.markdown("## Attendance Log (Latest 20 Records)")

# Log Placeholder (Local)
log_placeholder = st.empty()

def update_log_display(placeholder, local_logs):
    """Fetches the latest Supabase log and updates the Streamlit placeholder."""
    try:
        # Fetch latest logs from Supabase
        db_logs = supabase.table("attendance_log") \
                          .select("person_detected,timestamp") \
                          .order("timestamp", desc=True) \
                          .limit(20).execute().data
    except Exception:
        db_logs = []

    # Combining Database with Local Log
    # Using local_logs[::-1] ensures local logs are also newest-first for merging
    combined_logs = local_logs[::-1] + db_logs
    
    # Display Unique Logs
    seen_keys = set()
    unique_logs = []
    
    for entry in combined_logs:
        key = (entry.get("timestamp"), entry.get("person_detected"))
        if key not in seen_keys:
            seen_keys.add(key)
            unique_logs.append(entry)
    
    # Format & Display (Top 20 Newest Attendance Log)
    log_lines = []
    for entry in unique_logs[:20]:
        ts = entry.get("timestamp")
        pname = entry.get("person_detected")
        log_lines.append(f"**{ts}** — {pname}")

    placeholder.markdown("  \n".join(log_lines))

update_log_display(log_placeholder, st.session_state.local_log)


# Live Camera Feed
while cap.isOpened():
    # 2. Update Clock
    current_time = datetime.now().strftime("%H:%M:%S")
    current_date = datetime.now().strftime("%Y/%m/%d")
    # Use the placeholder to update the clock metric on every loop
    CLOCK_PLACEHOLDER.metric("Current Time", current_time, label_visibility="visible", help=current_date)


    ret, frame_bgr = cap.read()
    if not ret:
        st.error("Camera failed to load")
        break

    name, frame_bgr = detect_face_and_predict(frame_bgr)

    # Attendance Timer Logic
    if name is not None:
        if st.session_state.current_name != name:
            st.session_state.current_name = name
            st.session_state.start_time = time.time()
        else:
            elapsed = time.time() - st.session_state.start_time
            if elapsed >= DETECTION_DURATION:
                wib_tz = pytz.timezone('Asia/Jakarta')
                timestamp = datetime.now(wib_tz).strftime("[%Y-%m-%d] %H:%M:%S")

                # Update Local Log
                st.session_state.local_log.append({
                    "timestamp": timestamp,
                    "person_detected": name
                })
                
                # Update Database Log
                try:
                    supabase.table("attendance_log").insert({
                        "timestamp": timestamp,
                        "person_detected": name
                    }).execute()
                    
                    SUCCESS_MESSAGE_PLACEHOLDER.success(f"Attendance recorded for **{name}**")
                    
                    # Update log display (local_log is already up-to-date)
                    update_log_display(log_placeholder, st.session_state.local_log)

                except Exception as e:
                    SUCCESS_MESSAGE_PLACEHOLDER.error(f"Failed to log attendance: {e}")
                
                # Prevent Repeated Logging
                st.session_state.start_time = time.time() + 9999
    else:
        st.session_state.current_name = None
        st.session_state.start_time = None

    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    FRAME_WINDOW.image(frame_rgb)

cap.release()