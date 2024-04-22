import streamlit as st
from utils.navigation import get_authenticator

st.set_page_config(
    page_title="Intelligent BI",
    page_icon="👋",
)

authenticator = get_authenticator()
name, authentication_status, username = authenticator.login('main')

if authentication_status:
    st.switch_page("pages/mainpage.py")
elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
