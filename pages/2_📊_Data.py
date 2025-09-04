import streamlit as st
import pandas as pd
from pathlib import Path

st.title("📊 Data Explorer")

# ---- Load data (cached) ---
@st.cache_data
def load_data():
    p = Path(__file__).resolve().parents[1] / "assets" / "sample.csv"
    return pd.read_csv(p)

df = load_data()

st.subheader("Dataset")
st.dataframe(df, use_container_width=True)

st.subheader("Quick Summary")
st.write(df.describe())

st.subheader("Chart")
metric_col = st.selectbox("Choose a numeric column to chart", df.select_dtypes("number").columns)
st.line_chart(df[metric_col])
