import streamlit as st
from supabase_client import supabase
from datetime import datetime
import cv2
import time
import numpy as np
from utils.model import detect_face_and_predict  # ⬅ integrate your model
from PIL import Image

st.set_page_config(page_title="Veritas | Home")

# ===========================
# LOGIN CHECK
# ===========================
user = st.session_state.get("user")
if not user:
    st.warning("You must be logged in to use the Home page. Please login on the main page.")
    st.stop()

# ===========================
# SESSION STATE FOR TIMER
# ===========================
if "current_name" not in st.session_state:
    st.session_state.current_name = None

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "local_log" not in st.session_state:
    st.session_state.local_log = []

DETECTION_DURATION = 3.0  # seconds required for attendance

# ===========================
# LAYOUT
# ===========================
col1, col2 = st.columns([2, 1])

# ===========================
# CAMERA + MODEL INFERENCE
# ===========================
with col1:
    st.subheader("📷 Camera")

    FRAME_WINDOW = st.image([])

    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame_bgr = cap.read()
        if not ret:
            st.error("Camera failed to load")
            break

        # -------- ML DETECTION --------
        name, frame_bgr = detect_face_and_predict(frame_bgr)

        # -------- TIMER LOGIC --------
        if name is not None:
            # new person detected → reset timer
            if st.session_state.current_name != name:
                st.session_state.current_name = name
                st.session_state.start_time = time.time()
            else:
                # same person still detected
                elapsed = time.time() - st.session_state.start_time
                if elapsed >= DETECTION_DURATION:
                    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"

                    # log locally (always)
                    st.session_state.local_log.append({
                        "timestamp": timestamp,
                        "person_detected": name
                    })

                    # log to Supabase
                    try:
                        supabase.table("attendance_log").insert({
                            "user_email": user.get("email") if isinstance(user, dict) else user.email,
                            "person_detected": name
                        }).execute()
                        st.success(f"Attendance recorded for {name}")
                    except Exception as e:
                        st.error(f"Failed to log attendance: {e}")

                    # prevent repeated logging
                    st.session_state.start_time = time.time() + 9999
        else:
            st.session_state.current_name = None
            st.session_state.start_time = None

        # show frame on Streamlit
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        FRAME_WINDOW.image(frame_rgb)

# ===========================
# STATS + LOG PANEL
# ===========================
with col2:
    st.subheader("📊 Stats")

    capacity = int(st.secrets.get("ROOM_CAPACITY", 999))

    try:
        rows = supabase.table("attendance_log").select("*").order("timestamp", desc=True).limit(100).execute().data
        present_count = len(rows)
    except Exception:
        present_count = len(st.session_state.local_log)

    st.metric(label="Room Capacity", value=f"{present_count}/{capacity}")

    st.subheader("📝 Log")
    try:
        logs = supabase.table("attendance_log").select("person_detected,timestamp").order("timestamp", desc=True).limit(20).execute().data
    except Exception:
        logs = []

    combined = st.session_state.local_log[::-1] + logs

    for entry in combined[:20]:
        ts = entry.get("timestamp")
        pname = entry.get("person_detected")
        st.write(f"• {ts} — {pname}")

    # Logout
    if st.button("Logout"):
        from utils.auth import logout
        logout()
        st.rerun()
