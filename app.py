import streamlit as st
from utils import get_app_version

st.set_page_config(
    page_title="My Streamlit Template",
    page_icon="✨",
    layout="wide",
    menu_items={
        "Get Help": "https://docs.streamlit.io/",
        "Report a bug": "https://github.com/streamlit/streamlit/issues",
        "About": "A minimal multi-page app template."
    }
)

# --- Sidebar (persistent across pages) ---
with st.sidebar:
    st.header("✨ App")
    st.caption(f"Version: {get_app_version()}")
    st.divider()
    st.write("Use the menu at the top-left to switch pages.")
    st.markdown(
        """
        **Quick links**
        - 🏠 Home
        - 📊 Data
        - ⚙️ Settings
        """
    )

st.title("✨ My Streamlit Template")
st.write(
    "Welcome! Use the **Pages** menu (top-left) to navigate. "
    "This landing page is optional—feel free to keep content ultra-lean."
)

st.info(
    "Tip: Add global announcements here, or redirect users to a default page."
)
