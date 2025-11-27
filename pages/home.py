import streamlit as st
from supabase_client import supabase 
from datetime import datetim
from PIL import Image
import io

# from utils.insert_model import . . . 

st.set_page_config(page_title="Veritas | Home")

user = st.session_state.get("user")
if not user:
    st.warning("You must be logged in to use the Home page. Please login on the main page.")
    st.stop()

col1, col2 = st.columns([2, 1])

# Initialize local log in session
if "local_log" not in st.session_state:
    st.session_state.local_log = []

# Camera Box
# with col1:
#     st.subheader("📷 Camera")
#     cam_file = st.camera_input("Start camera and take photo")

#     if cam_file is not None:
#         # read image into PIL
#         image = Image.open(cam_file)
#         st.image(image, caption="Captured image", use_column_width=True)

#     # Run model inference (replace with your real call)
#     with st.spinner("Analyzing..."):
#         detected_name = predict_image(image)

#     # Save to supabase
#     try:
#         resp = supabase.table("attendance_log").insert({
#         "user_email": user.get("email") if isinstance(user, dict) else user.email,
#         "person_detected": detected_name
#         }).execute()
#         st.success(f"Detected: {detected_name} — logged to database")
#     except Exception as e:
#         st.error(f"Detected {detected_name} but failed to save: {e}")


#     # Also append to session local log for immediate display
#     timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
#     st.session_state.local_log.append({
#         "timestamp": timestamp,
#         "person_detected": detected_name
#     })

with col2:
    st.subheader("📊 Stats")
    # Room capacity from secrets or default
    capacity = int(st.secrets.get("ROOM_CAPACITY", 999))

    # Count present today (simple query: count rows where date = today)
    try:
        # crude: fetch today rows (Postgres timestamptz comparison)
        today_rows = supabase.table("attendance_log").select("id", count="exact").execute()
        present_count = 0
        # If above fails, fallback to fetching limited rows
        rows = supabase.table("attendance_log").select("*").order("timestamp", desc=True).limit(100).execute().data
        if isinstance(rows, list):
            present_count = len(rows)
    except Exception:
        present_count = len(st.session_state.local_log)

    st.metric(label="Room Capacity", value=f"{present_count}/{capacity}")

    st.subheader("📝 Log")
    # show most recent logs: mix DB + session
    try:
        logs = supabase.table("attendance_log").select("person_detected,timestamp").order("timestamp", desc=True).limit(20).execute().data
    except Exception:
        logs = []


    # prefer server logs but include local ones
    combined = []
    if logs:
        for r in logs:
            combined.append({
            "timestamp": r.get("timestamp"),
            "person_detected": r.get("person_detected")
            })
        # append local ones not yet in server
    combined = st.session_state.local_log[::-1] + combined


    for entry in combined[:20]:
        ts = entry.get("timestamp")
        name = entry.get("person_detected")
        st.write(f"• {ts} — {name}")


    # Logout
if st.button("Logout"):
    from utils.auth import logout
    logout()
    st.experimental_rerun()
