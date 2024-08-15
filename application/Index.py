import streamlit as st
from utils.navigation import get_authenticator, force_set_cookie

st.set_page_config(
    page_title="Generative BI",
    page_icon="👋",
)

authenticator = get_authenticator()
name, authentication_status, username = authenticator.login('main')

if authentication_status:
    force_set_cookie(authenticator)
    st.switch_page("pages/mainpage.py")
elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
