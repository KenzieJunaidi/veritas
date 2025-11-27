import streamlit as st
from utils.auth import login, signup

st.set_page_config(page_title="Veritas | Login")

if "initialized" not in st.session_state:
    st.session_state.initialized = True

st.title("Veritas")
st.write("Camera-based Attendance System - Login or Register")

tab1, tab2 = st.tabs(["Login", "Register"])

with tab1:
    st.header("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        ok, msg = login(email, password)

        if ok:
            st.success(msg)
            st.experimental_rerun()
        
        else:
            st.error(msg)

with tab2:
    st.header("Register")
    reg_email = st.text_input("Email", key="reg_email")
    reg_password = st.text_input("Password", type="password", key="reg_password")

    if st.button("Create Account"):
        ok, msg = signup(reg_email, reg_password)

        if ok:
            st.success(msg)
        else:
            st.error(msg)