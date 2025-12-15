import streamlit as st
from supabase_client import supabase

def signup(email: str, password: str):
    try:
        supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        return True, "Check your email for confirmation link."
    except Exception as e:
        return False, str(e)

def login(email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        user = res.user if hasattr(res, "user") else res.get("user")

        if user:
            st.session_state["user"] = user
            return True, "Login successful"

        return False, "Invalid credentials"

    except Exception as e:
        return False, str(e)

def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.pop("user", None)
