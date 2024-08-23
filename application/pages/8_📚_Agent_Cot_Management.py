import time

import streamlit as st
from dotenv import load_dotenv
import logging
from nlq.business.profile import ProfileManagement
from nlq.business.vector_store import VectorStore
from utils.navigation import make_sidebar
from utils.env_var import opensearch_info

logger = logging.getLogger(__name__)

def delete_entity_sample(profile_name, id):
    VectorStore.delete_agent_cot_sample(profile_name, id)
    st.success(f'Sample {id} deleted.')


def main():
    load_dotenv()
    logger.info('start agent cot management')
    st.set_page_config(page_title="Agent Cot Management", )
    make_sidebar()

    if 'profile_page_mode' not in st.session_state:
        st.session_state['index_mgt_mode'] = 'default'

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

    if "profiles_list" not in st.session_state:
        st.session_state["profiles_list"] = []

    if "update_profile" not in st.session_state:
        st.session_state.update_profile = False

    if 'profiles' not in st.session_state:
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        st.session_state['profiles'] = all_profiles
        st.session_state["profiles_list"] = list(all_profiles.keys())

    if st.session_state.update_profile:
        logger.info("session_state update_profile get_all_profiles_with_info")
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        st.session_state["profiles_list"] = list(all_profiles.keys())
        st.session_state['profiles'] = all_profiles
        st.session_state.update_profile = False

    with st.sidebar:
        st.title("Agent Cot Management")
        all_profiles_list = st.session_state["profiles_list"]
        if st.session_state.current_profile != "" and st.session_state.current_profile in all_profiles_list:
            profile_index = all_profiles_list.index(st.session_state.current_profile)
            current_profile = st.selectbox("My Data Profiles", all_profiles_list, index=profile_index)
        else:
            current_profile = st.selectbox("My Data Profiles", all_profiles_list,
                                       index=None,
                                       placeholder="Please select data profile...", key='current_profile_name')

    tab_view, tab_add, tab_search = st.tabs(['View Samples', 'Add New Sample', 'Sample Search'])
    if current_profile is not None:
        st.session_state['current_profile'] = current_profile
        with tab_view:
            if current_profile is not None:
                st.write("The display page can show a maximum of 5000 pieces of data")
                for sample in VectorStore.get_all_agent_cot_samples(current_profile):
                    # st.write(f"Sample: {sample}")
                    with st.expander(sample['query']):
                        st.code(sample['comment'])
                        st.button('Delete ' + sample['id'], on_click=delete_entity_sample, args=[current_profile, sample['id']])

        with tab_add:
            if current_profile is not None:
                query = st.text_input('Query', key='index_question')
                comment = st.text_area('Comment', key='index_answer', height=300)

                if st.button('Submit', type='primary'):
                    if len(query) > 0 and len(comment) > 0:
                        VectorStore.add_agent_cot_sample(current_profile, query, comment)
                        st.success('Sample added')
                        time.sleep(2)
                        # del st.session_state['index_question']
                        # del st.session_state['index_answer']
                        st.rerun()
                    else:
                        st.error('please input valid question and answer')

        with tab_search:
            if current_profile is not None:
                entity_search = st.text_input('Entity Search', key='index_entity_search')
                retrieve_number = st.slider("Entity Retrieve Number", 0, 100, 10)
                if st.button('Search', type='primary'):
                    if len(entity_search) > 0:
                        search_sample_result = VectorStore.search_sample(current_profile, retrieve_number, opensearch_info['agent_index'],
                                                                         entity_search)
                        for sample in search_sample_result:
                            sample_res = {'Score': sample['_score'],
                                          'Entity': sample['_source']['query'],
                                          'Answer': sample['_source']['comment'].strip()}
                            st.code(sample_res)
                            st.button('Delete ' + sample['_id'], key=sample['_id'], on_click=delete_entity_sample,
                                      args=[current_profile, sample['_id']])
    else:
        st.info('Please select data profile in the left sidebar.')

if __name__ == '__main__':
    main()
