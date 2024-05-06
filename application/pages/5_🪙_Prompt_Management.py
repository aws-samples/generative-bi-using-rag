import streamlit as st
from dotenv import load_dotenv
import logging
from nlq.business.profile import ProfileManagement
from utils.navigation import make_sidebar

logger = logging.getLogger(__name__)


def main():
    load_dotenv()
    logger.info('start prompt management')
    st.set_page_config(page_title="Prompt Management")
    make_sidebar()

    with st.sidebar:
        st.title("Prompt Management")
        current_profile = st.selectbox("My Data Profiles", ProfileManagement.get_all_profiles(),
                                       index=None,
                                       placeholder="Please select data profile...", key='current_profile_name')

    if current_profile is not None:
        profile_detail = ProfileManagement.get_profile_by_name(current_profile)

        system_prompt = profile_detail.system_prompt
        user_prompt = profile_detail.user_prompt
        if system_prompt is not None and user_prompt is not None:
            model_selected_table = st.selectbox("LLM Model", system_prompt.keys(), index=None,
                                                placeholder="Please select a model")
            if model_selected_table is not None:
                system_prompt_input = st.text_area('System Prompt', system_prompt[model_selected_table])
                user_prompt_input = st.text_area('User Prompt', user_prompt[model_selected_table], height=500)

                if st.button('Save', type='primary'):
                    # assign new system/user prompt by selected model
                    system_prompt[model_selected_table] = system_prompt_input
                    user_prompt[model_selected_table] = user_prompt_input

                    # save new profile to DynamoDB
                    ProfileManagement.update_table_prompt(current_profile, system_prompt, user_prompt)
                    st.success('saved.')
    else:
        st.info('Please select data profile in the left sidebar.')


if __name__ == '__main__':
    main()
