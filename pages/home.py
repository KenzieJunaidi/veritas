import streamlit as st
from supabase_client import supabase
from datetime import datetime
import cv2
import time
import numpy as np
from utils.model import detect_face_and_predict
from PIL import Image

st.set_page_config(page_title="Veritas | Home", layout="wide")

# ========================================================
# CSS INJECTION TO SET A CUSTOM MAXIMUM WIDTH
# ========================================================
st.markdown(
    """
    <style>
    /* 1. Set Custom Max-Width for the main content area (The Intermediate Width) */
    div.block-container {
        max-width: 1300px; /* Adjust this value (e.g., 1000px - 1400px) */
    }

    /* 2. Reduce the gap between the columns (Camera Feed and Stats Panel) */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem; /* Adjust this value (0.5rem for small, 1rem for moderate) */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ===========================
# LOGIN CHECK
# ===========================
user = st.session_state.get("user")
if not user:
    st.warning("You must be logged in to use the Home page. Please login on the main page.")
    st.stop()

# ===========================
# SESSION STATE
# ===========================
if "current_name" not in st.session_state:
    st.session_state.current_name = None

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "local_log" not in st.session_state:
    st.session_state.local_log = []

DETECTION_DURATION = 1.5  # seconds to confirm attendance

# ===========================
# TOP RIGHT LOGOUT BUTTON
# ===========================
top_left, top_right = st.columns([8, 1])

with top_right:
    if st.button("Logout"):
        from utils.auth import logout
        logout()
        st.rerun()

# ===========================
# MAIN LAYOUT – CAMERA & STATS
# ===========================
col1, col2 = st.columns([2, 1])

# Placeholder for the success notification
SUCCESS_MESSAGE_PLACEHOLDER = st.empty()


# ===========================
# CAMERA PANEL
# ===========================
with col1:
    st.markdown("## Live Camera Feed")
    FRAME_WINDOW = st.image([])

    cap = cv2.VideoCapture(0)
    camera_status = "🔴 Not Connected"

    if cap.isOpened():
        camera_status = "🟢 Active (ID: 10)"
    else:
        camera_status = "🔴 Failed to Load"

# ===========================
# STATS PANEL
# ===========================
with col2:
    st.markdown("## System Status (Demo)")

    # decorative stats
    class_name = "A0707"
    model_status = "🧠 Model Loaded"
    connection_status = camera_status
    demo_fps = 30.00

    st.metric("Class", class_name)
    st.metric("Camera Status", connection_status)
    st.metric("Model Status", model_status)
    st.metric("FPS", demo_fps)

# ===============================================
# FULL-WIDTH ATTENDANCE LOG (MOVED TO HERE)
# ===============================================
st.markdown("---")
st.markdown("## Attendance Log (Latest 20 Records)")

# Create a placeholder to dynamically update the log inside the loop
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

    # Combine local and DB logs (local_log is already in reverse order for newest first)
    # NOTE: local_logs is passed as st.session_state.local_log[::-1] (reversed)
    combined_logs = local_logs + db_logs
    
    # ----------------------------------------------------
    # FIX: Deduplicate entries before display
    # ----------------------------------------------------
    seen_keys = set()
    unique_logs = []
    
    # Iterate through the combined logs, keeping the first instance found
    # This naturally prioritizes the local log if it appears first
    for entry in combined_logs:
        # Use a tuple of the identifying fields as a unique key
        key = (entry.get("timestamp"), entry.get("person_detected"))
        if key not in seen_keys:
            seen_keys.add(key)
            unique_logs.append(entry)
    # ----------------------------------------------------
    
    # Format and display the top 20 unique logs
    log_lines = []
    for entry in unique_logs[:20]:
        ts = entry.get("timestamp")
        pname = entry.get("person_detected")
        log_lines.append(f"**{ts}** — {pname}")

    placeholder.markdown("  \n".join(log_lines))

# Initial log load
update_log_display(log_placeholder, st.session_state.local_log[::-1])


# ===========================
# CAMERA LOOP (RUNS AFTER UI)
# ===========================
while cap.isOpened():
    ret, frame_bgr = cap.read()
    if not ret:
        st.error("Camera failed to load")
        break

    # ---- Inference ----
    name, frame_bgr = detect_face_and_predict(frame_bgr)

    # ---- Attendance timer logic ----
    if name is not None:
        if st.session_state.current_name != name:
            st.session_state.current_name = name
            st.session_state.start_time = time.time()
        else:
            elapsed = time.time() - st.session_state.start_time
            if elapsed >= DETECTION_DURATION:
                timestamp = datetime.utcnow().strftime("[%Y-%m-%d] %H:%M:%S")

                # 1. Update local log
                st.session_state.local_log.append({
                    "timestamp": timestamp,
                    "person_detected": name
                })
                
                # Reverse local log for display order (newest first)
                local_logs_for_display = st.session_state.local_log[::-1]

                # 2. Log to Supabase
                try:
                    supabase.table("attendance_log").insert({
                        "timestamp": timestamp,
                        "person_detected": name
                    }).execute()
                    
                    # Display the success message in the placeholder
                    SUCCESS_MESSAGE_PLACEHOLDER.success(f"Attendance recorded for **{name}**")
                    
                    # 3. Update the displayed log immediately after success
                    update_log_display(log_placeholder, local_logs_for_display)

                except Exception as e:
                    SUCCESS_MESSAGE_PLACEHOLDER.error(f"Failed to log attendance: {e}")

                # Prevent immediate re-log for the same person
                st.session_state.start_time = time.time() + 9999
    else:
        st.session_state.current_name = None
        st.session_state.start_time = None

    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    FRAME_WINDOW.image(frame_rgb)

cap.release()