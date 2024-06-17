import streamlit as st
from utils.navigation import make_sidebar

st.set_page_config(
    page_title="Generative BI",
    page_icon="👋",
)

make_sidebar()

st.write("## Welcome to Generative BI using RAG on AWS!👋")

st.sidebar.success("Select a demo above.")

st.markdown(
    """
In the data analysis scenario, analysts often need to write multi-round, complex query statements to obtain business insights.

Amazon Web Services (AWS) has built an intelligent data analysis assistant solution to address this scenario. Leveraging the powerful natural language understanding capabilities of large language models, non-technical users can query and analyze data through natural language, without needing to master SQL or other professional skills, helping business users obtain data insights and improve decision-making efficiency. 

This guide is based on services such as Amazon Bedrock, Amazon OpenSearch, and Amazon DynamoDB.
"""
)
