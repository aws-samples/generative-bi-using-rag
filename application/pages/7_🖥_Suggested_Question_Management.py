import streamlit as st
from dotenv import load_dotenv
from loguru import logger
from nlq.business.suggested_question import SuggestedQuestionManagement as sqm
from utils.constant import ACTIVE_PROMPT_NAME


def main():
    load_dotenv()
    logger.info('Start suggested question management')
    st.set_page_config(page_title="Suggested Question Management", )
    
    active_prompt = sqm.get_prompt_by_name(ACTIVE_PROMPT_NAME)
    col_annotation = st.text_area('Prompt to generate suggested question', active_prompt, height=500)

    if st.button('Save', type='primary'):
        new_prompt = col_annotation
        sqm.update_prompt(new_prompt)
        st.success('Prompt saved.')
    
    if st.button('Reset to Default'):
        new_prompt = col_annotation
        sqm.reset_to_default()
        # TODO: update UI as default value
        st.success('Reset to default.')


if __name__ == '__main__':
    main()
