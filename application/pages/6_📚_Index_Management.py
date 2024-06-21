import time

import streamlit as st
from dotenv import load_dotenv
import logging
from nlq.business.profile import ProfileManagement
from nlq.business.vector_store import VectorStore
from utils.navigation import make_sidebar
from utils.env_var import opensearch_info

logger = logging.getLogger(__name__)

def delete_sample(profile_name, id):
    VectorStore.delete_sample(profile_name, id)
    st.success(f'Sample {id} deleted.')


def main():
    load_dotenv()
    logger.info('start index management')
    st.set_page_config(page_title="Index Management", )
    make_sidebar()

    if 'profile_page_mode' not in st.session_state:
        st.session_state['index_mgt_mode'] = 'default'

    with st.sidebar:
        st.title("Index Management")
        current_profile = st.selectbox("My Data Profiles", ProfileManagement.get_all_profiles(),
                                       index=None,
                                       placeholder="Please select data profile...", key='current_profile_name')

    tab_view, tab_add, tab_search = st.tabs(['View Samples', 'Add New Sample', 'Sample Search'])

    if current_profile is not None:
        with tab_view:
            if current_profile is not None:
                st.write("The display page can show a maximum of 5000 pieces of data")
                for sample in VectorStore.get_all_samples(current_profile):
                    with st.expander(sample['text']):
                        st.code(sample['sql'])
                        st.button('Delete ' + sample['id'], on_click=delete_sample, args=[current_profile, sample['id']])

        with tab_add:
            if current_profile is not None:
                question = st.text_input('Question', key='index_question')
                answer = st.text_area('Answer(SQL)', key='index_answer', height=300)

                if st.button('Submit', type='primary'):
                    if len(question) > 0 and len(answer) > 0:
                        VectorStore.add_sample(current_profile, question, answer)
                        st.success('Sample added')
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error('please input valid question and answer')
        with tab_search:
            if current_profile is not None:
                entity_search = st.text_input('Question Search', key='index_entity_search')
                retrieve_number = st.slider("Question Retrieve Number", 0, 100, 10)
                if st.button('Search', type='primary'):
                    if len(entity_search) > 0:
                        search_sample_result = VectorStore.search_sample(current_profile, retrieve_number, opensearch_info['sql_index'],
                                                                         entity_search)
                        for sample in search_sample_result:
                            sample_res = {'Score': sample['_score'],
                                          'Entity': sample['_source']['text'],
                                          'Answer': sample['_source']['sql'].strip()}
                            st.code(sample_res)
                            st.button('Delete ' + sample['_id'], key=sample['_id'], on_click=delete_sample,
                                      args=[current_profile, sample['_id']])
    else:
        st.info('Please select data profile in the left sidebar.')
        

if __name__ == '__main__':
    main()
