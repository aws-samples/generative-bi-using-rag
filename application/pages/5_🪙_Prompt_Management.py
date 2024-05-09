import streamlit as st
from dotenv import load_dotenv
import logging
from nlq.business.profile import ProfileManagement
from utils.navigation import make_sidebar

logger = logging.getLogger(__name__)

"""
prompt dynamoDB 存储格式
prompt_map_dict = {
    'text2sql': {
        'title': 'Text2SQL Prompt',
        'system_prompt': system_prompt_dict,
        'user_prompt': user_prompt_dict
    },
    'intent': {
        'title': 'Intent Prompt',
        'system_prompt': intent_system_prompt_dict,
        'user_prompt': intent_user_prompt_dict
    },
    'knowledge': {
        'title': 'Knowledge Prompt',
        'system_prompt': knowledge_system_prompt_dict,
        'user_prompt': knowledge_user_prompt_dict
    },
    'agent': {
        'title': 'Agent Task Prompt',
        'system_prompt': agent_system_prompt_dict,
        'user_prompt': agent_user_prompt_dict
    },
    'agent_analyse': {
        'title': 'Agent Data Analyse Prompt',
        'system_prompt': agent_analyse_system_prompt_dict,
        'user_prompt': agent_analyse_user_prompt_dict
    },
    'data_summary': {
        'title': 'Data Summary Prompt',
        'system_prompt': data_summary_system_prompt_dict,
        'user_prompt': data_summary_user_prompt_dict
    },
    'data_visualization': {
        'title': 'Data Visualization Prompt',
        'system_prompt': data_visualization_system_prompt_dict,
        'user_prompt': data_visualization_user_prompt_dict
    },
    'suggestion': {
        'title': 'Suggest Question Prompt',
        'system_prompt': suggest_question_system_prompt_dict,
        'user_prompt': suggest_question_user_prompt_dict
    }
}
"""
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

        prompt_map = profile_detail.prompt_map
        if prompt_map is not None:
            prompt_type_selected_table = st.selectbox("Prompt Type", prompt_map.keys(), index=None,
                                                      format_func=lambda x: prompt_map[x].get('title'),
                                                      placeholder="Please select a prompt type")

            if prompt_type_selected_table is not None:
                single_type_prompt_map = prompt_map.get(prompt_type_selected_table)
                system_prompt = single_type_prompt_map.get('system_prompt')
                user_prompt = single_type_prompt_map.get('user_prompt')
                model_selected_table = st.selectbox("LLM Model", system_prompt.keys(), index=None,
                                                    placeholder="Please select a model")

                if model_selected_table is not None:
                    system_prompt_input = st.text_area('System Prompt', system_prompt[model_selected_table], height=300)
                    user_prompt_input = st.text_area('User Prompt', user_prompt[model_selected_table], height=500)

                    if st.button('Save', type='primary'):
                        # assign new system/user prompt by selected model
                        system_prompt[model_selected_table] = system_prompt_input
                        user_prompt[model_selected_table] = user_prompt_input

                        # save new profile to DynamoDB
                        ProfileManagement.update_table_prompt_map(current_profile, prompt_map)
                        st.success('saved.')

    else:
        st.info('Please select data profile in the left sidebar.')


if __name__ == '__main__':
    main()
