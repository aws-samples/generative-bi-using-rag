import streamlit as st

from nlq.business.vector_store import VectorStore
from utils.navigation import make_sidebar
from utils.opensearch import opensearch_index_init

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

# Check OpenSearch Index Init and Test Embedding Insert
opensearch_index_init = opensearch_index_init()
if not opensearch_index_init:
    st.info("The OpenSearch Index is Error, Please Create OpenSearch Index First!!!")
else:
    current_profile = "entity_insert_test"
    entity = "环比"
    comment = "环比增长率是指本期和上期相比较的增长率，计算公式为：环比增长率 =（本期数－上期数）/ 上期数 ×100%"
    VectorStore.add_entity_sample(current_profile, entity, comment)
