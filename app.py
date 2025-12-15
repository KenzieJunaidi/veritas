import time
import streamlit as st
from utils.auth import login, signup

# MUST be first Streamlit command
st.set_page_config(
    page_title="Veritas",
    page_icon="🔐",
    layout="centered"
)

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


def login_dashboard():
    st.title("Veritas")
    st.write("Secure, Touchless Attendance powered by AI Face Recognition.")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.header("Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            ok, msg = login(email, password)

            if ok:
                st.success(msg)
                st.session_state.logged_in = True
                time.sleep(1)
                st.switch_page("Home")
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


# Run app
login_dashboard()
