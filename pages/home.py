import streamlit as st
from supabase_client import supabase
from datetime import datetime
from utils.model import detect_face_and_predict
from PIL import Image
import numpy as np
import pytz

st.set_page_config(page_title="Veritas | Home", layout="wide")

# Login Check
user = st.session_state.get("user")
if not user:
    st.warning("You must be logged in.")
    st.stop()

# Logout
if st.button("Logout"):
    from utils.auth import logout
    logout()
    st.switch_page("app.py")

st.title("Veritas – Attendance")

# Camera Input (Cloud-Compatible)
image = st.camera_input("Take a photo for attendance")

if image:
    img = Image.open(image).convert("RGB")
    frame = np.array(img)

    name, annotated_frame = detect_face_and_predict(frame)

    st.image(annotated_frame, caption="Processed Image")

    if name:
        wib = pytz.timezone("Asia/Jakarta")
        timestamp = datetime.now(wib).strftime("[%Y-%m-%d] %H:%M:%S")

        try:
            supabase.table("attendance_log").insert({
                "timestamp": timestamp,
                "person_detected": name
            }).execute()

            st.success(f"Attendance recorded for **{name}**")

        except Exception as e:
            st.error(f"Failed to log attendance: {e}")
    else:
        st.warning("No face detected")

# Attendance Log
st.markdown("## Latest Attendance")

logs = supabase.table("attendance_log") \
    .select("person_detected,timestamp") \
    .order("timestamp", desc=True) \
    .limit(20).execute().data

for log in logs:
    st.write(f"**{log['timestamp']}** — {log['person_detected']}")
