import streamlit as st
import streamlit_authenticator as stauth
from time import sleep
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.source_util import get_pages
import yaml
from yaml.loader import SafeLoader


def get_authenticator():
    with open('config_files/stauth_config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    return stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['pre-authorized']
    )


def get_current_page_name():
    ctx = get_script_run_ctx()
    if ctx is None:
        raise RuntimeError("Couldn't get script context")

    pages = get_pages("")

    return pages[ctx.page_script_hash]["page_name"]


def make_sidebar():
    with st.sidebar:
        if st.session_state.get('authentication_status'):
            st.page_link("pages/mainpage.py", label="Index")
            st.page_link("pages/1_🌍_Generative_BI_Playground.py", label="Generative BI Playground", icon="🌍")
            st.markdown(":gray[Data Customization Management]", help='Add your own datasources and customize description for LLM to better understand them')
            st.page_link("pages/2_🪙_Data_Connection_Management.py", label="Data Connection Management", icon="🪙")
            st.page_link("pages/3_🪙_Data_Profile_Management.py", label="Data Profile Management", icon="🪙")
            st.page_link("pages/4_🪙_Schema_Description_Management.py", label="Schema Description Management", icon="🪙")
            st.page_link("pages/5_🪙_Prompt_Management.py", label="Prompt Management", icon="🪙")
            st.markdown(":gray[Performance Enhancement]", help='Optimize your LLM for better performance by adding RAG or agent')
            st.page_link("pages/6_📚_Index_Management.py", label="Index Management", icon="📚")
            st.page_link("pages/7_📚_Entity_Management.py", label="Entity Management", icon="📚")
            st.page_link("pages/8_📚_Agent_Cot_Management.py", label="Agent Cot Management", icon="📚")

            if st.button("Log out"):
                logout()

        elif get_current_page_name() != "Index":
            # If anyone tries to access a secret page without being logged in,
            # redirect them to the login page
            st.switch_page("Index.py")


def logout():
    authenticator = get_authenticator()
    authenticator.logout('Logout', 'unrendered')
    st.info("Logged out successfully!")
    sleep(0.5)
    st.switch_page("Index.py")
