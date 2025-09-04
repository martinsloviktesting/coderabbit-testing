import streamlit as st

st.title("🏠 Home")
st.write("A friendly welcome page.")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Session Snapshot")
    st.json(st.session_state)

with col2:
    st.subheader("Actions")
    if st.button("Clear session state"):
        # Wipe keys except Streamlit internals
        for k in list(st.session_state.keys()):
            if not k.startswith("_"):
                del st.session_state[k]
        st.success("Session state cleared.")
