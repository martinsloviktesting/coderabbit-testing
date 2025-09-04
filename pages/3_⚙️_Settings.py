import streamlit as st

st.title("⚙️ Settings")

st.write("Settings are stored in `st.session_state` for a simple, stateful UX.")

# Defaults
if "username" not in st.session_state:
    st.session_state["username"] = "Guest"
if "refresh_secs" not in st.session_state:
    st.session_state["refresh_secs"] = 10
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False

with st.form("settings_form"):
    username = st.text_input("Display name", st.session_state["username"])
    refresh_secs = st.number_input("Auto-refresh interval (seconds)", min_value=1, max_value=300,
                                   value=st.session_state["refresh_secs"], step=1)
    dark_mode = st.checkbox("Enable dark mode (demo toggle only)", value=st.session_state["dark_mode"])

    submitted = st.form_submit_button("Save Settings")
    if submitted:
        st.session_state["username"] = username
        st.session_state["refresh_secs"] = int(refresh_secs)
        st.session_state["dark_mode"] = dark_mode
        st.success("Settings saved to session.")

st.divider()
st.subheader("Current Settings")
st.json({
    "username": st.session_state["username"],
    "refresh_secs": st.session_state["refresh_secs"],
    "dark_mode": st.session_state["dark_mode"]
})
