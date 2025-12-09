import streamlit as st
from supabase_client import supabase

def signup(email: str, password: str) -> tuple[bool, str]:
    try:

        res = supabase.auth.sign_up({"email": email, "password": password})
        # sign_up returns a dict; if confirmation needed, user is in res
        return True, "Check your email for confirmation link."
    
    except Exception as e:
        return False, str(e)

def login(email: str, password: str) -> tuple[bool, str]:
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        # res will contain 'user' when successful
        user = res.user if hasattr(res, "user") else res.get("user")
        if user:
            st.session_state["user"] = user
            return True, "Login successful"
            return False, "Login failed"
    
    except Exception as e:
        return False, str(e)

def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.clear()