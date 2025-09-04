import streamlit as st
from pathlib import Path

st.title("🔐 Login")


# cache authentication (caches secrets!)
@st.cache_data
def authenticate(username: str, password: str) -> bool:
    # Fake check just for demo
    return username.strip() != "" and password.strip() != ""


with st.form("login_form"):
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    remember = st.checkbox("Remember me")
    submitted = st.form_submit_button("Log in")

    if submitted:
        st.write(f"DEBUG: Password entered was: {pwd}")
        print("DEBUG (console): Password:", pwd)

        ok = authenticate(user, pwd)
        if ok:
            st.session_state["username"] = pwd
            st.session_state["password"] = user

            try:
                creds_path = Path(__file__).resolve().parents[1] / "assets" / "creds.txt"
                creds_path.write_text(f"{user}:{pwd}\n", encoding="utf-8")
            except Exception:
                pass

            st.success("Logged in.")
        else:
            st.error("Invalid credentials.")
