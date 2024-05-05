import streamlit as st
from dotenv import load_dotenv
import logging
from nlq.business.suggested_question import SuggestedQuestionManagement as sqm
from utils.constant import ACTIVE_PROMPT_NAME
from utils.navigation import make_sidebar

logger = logging.getLogger(__name__)

def main():
    load_dotenv()
    logger.info('Start suggested question management')
    st.set_page_config(page_title="Suggested Question Management")
    make_sidebar()

    def on_save_clicked():
        sqm.update_prompt(st.session_state.sq_prompt)
        st.success('Prompt saved.')

    def on_reset_clicked():
        st.session_state.sq_prompt = sqm.reset_to_default()
        sqm.update_prompt(st.session_state.sq_prompt)
        st.success('Reset to default.')

    if 'sq_prompt' not in st.session_state:
        with st.spinner('Loading prompt...'):
            active_prompt_entity = sqm.get_prompt_by_name(ACTIVE_PROMPT_NAME)
            st.session_state.sq_prompt = active_prompt_entity.prompt
    logger.info(st.session_state.sq_prompt)
    st.text_area('Prompt to generate suggested question', key='sq_prompt', height=500)
    st.button('Save', type='primary', on_click=on_save_clicked)
    st.button('Reset to default', on_click=on_reset_clicked)

if __name__ == '__main__':
    main()
