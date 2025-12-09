import time
import streamlit as st
from utils.auth import login, signup

# Login / Register Page Layout
def login_dashboard():
    st.set_page_config(page_title="Veritas")

    if "initialized" not in st.session_state:
        st.session_state.initialized = True

    st.title("Veritas")
    st.write("Secure, Touchless Attendance powered by AI Face Recognition.")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.header("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            ok, msg = login(email, password)

            if ok:
                st.success(msg)
                time.sleep(1)
                st.switch_page("pages/Home.py")
            
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

home_page = st.Page(login_dashboard, title="Login", icon=":material/key:")
report_page = st.Page("pages/Home.py", title="Home", icon=":material/home:")

selected_page = st.navigation([home_page, report_page])
selected_page.run()