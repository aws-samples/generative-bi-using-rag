import streamlit as st
from utils.navigation import make_sidebar

st.set_page_config(
    page_title="Generative BI",
    page_icon="👋",
)

make_sidebar()

st.write("## Welcome to Generative BI Playground!👋")

st.sidebar.success("Select a demo above.")

st.markdown(
    """
    Welcome to the Natural Language Querying Playground! This interactive application is designed to bridge the gap between natural language and databases. Enter your query in plain English, and watch as it's transformed into a SQL or Pandas command. The result can then be visualized, giving you insights without needing to write any code. Experiment, learn, and see the power of NLQ in action!
"""
)
