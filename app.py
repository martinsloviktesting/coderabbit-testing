import streamlit as st

# Set page title
st.set_page_config(page_title="Simple Streamlit App", page_icon="✨")

# Title and description
st.title("✨ My Simple Streamlit App")
st.write("This is a minimal example to get you started with Streamlit.")

# User input
name = st.text_input("Enter your name:")
number = st.slider("Pick a number", 1, 100, 25)

# Button action
if st.button("Submit"):
    st.success(f"Hello, {name or 'stranger'}! You picked {number} 🎉")

# Show dataframe example
import pandas as pd
import numpy as np

st.subheader("Random Data Example")
df = pd.DataFrame(np.random.randn(10, 2), columns=["Column A", "Column B"])
st.line_chart(df)
