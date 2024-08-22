import time

import pandas as pd
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


def read_file(uploaded_file):
    """
    read upload csv file
    :param uploaded_file:
    :return:
    """
    file_type = uploaded_file.name.split('.')[-1].lower()
    if file_type == 'csv':
        uploaded_data = pd.read_csv(uploaded_file)
    elif file_type in ['xls', 'xlsx']:
        uploaded_data = pd.read_excel(uploaded_file)
    else:
        st.error(f"Unsupported file type: {file_type}")
        return None
    columns = list(uploaded_data.columns)
    if "question" in columns and "sql" in columns:
        return uploaded_data
    else:
        st.error(f"The columns need contains question and sql")
        return None


def main():
    load_dotenv()
    logger.info('start index management')
    st.set_page_config(page_title="Index Management", )
    make_sidebar()

    if 'profile_page_mode' not in st.session_state:
        st.session_state['index_mgt_mode'] = 'default'

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

    if "update_profile" not in st.session_state:
        st.session_state.update_profile = False

    if "profiles_list" not in st.session_state:
        st.session_state["profiles_list"] = []

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
        st.title("Index Management")
        all_profiles_list = st.session_state["profiles_list"]
        if st.session_state.current_profile != "" and st.session_state.current_profile in all_profiles_list:
            profile_index = all_profiles_list.index(st.session_state.current_profile)
            current_profile = st.selectbox("My Data Profiles", all_profiles_list, index=profile_index)
        else:
            current_profile = st.selectbox("My Data Profiles", all_profiles_list,
                                           index=None,
                                           placeholder="Please select data profile...", key='current_profile_name')

    tab_view, tab_add, tab_search, batch_insert = st.tabs(
        ['View Samples', 'Add New Sample', 'Sample Search', 'Batch Insert Samples'])

    if current_profile is not None:
        st.session_state['current_profile'] = current_profile
        with tab_view:
            if current_profile is not None:
                st.write("The display page can show a maximum of 5000 pieces of data")
                for sample in VectorStore.get_all_samples(current_profile):
                    with st.expander(sample['text']):
                        st.code(sample['sql'])
                        st.button('Delete ' + sample['id'], on_click=delete_sample,
                                  args=[current_profile, sample['id']])

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
                        search_sample_result = VectorStore.search_sample(current_profile, retrieve_number,
                                                                         opensearch_info['sql_index'],
                                                                         entity_search)
                        for sample in search_sample_result:
                            sample_res = {'Score': sample['_score'],
                                          'Entity': sample['_source']['text'],
                                          'Answer': sample['_source']['sql'].strip()}
                            st.code(sample_res)
                            st.button('Delete ' + sample['_id'], key=sample['_id'], on_click=delete_sample,
                                      args=[current_profile, sample['_id']])
        with batch_insert:
            if current_profile is not None:
                st.write("This page support CSV or Excel files batch insert sql samples.")
                st.write("**The Column Name need contain 'question' and 'sql'**")
                uploaded_files = st.file_uploader("Choose CSV or Excel files", accept_multiple_files=True,
                                                  type=['csv', 'xls', 'xlsx'])
                if uploaded_files:
                    for i, uploaded_file in enumerate(uploaded_files):
                        status_text = st.empty()
                        status_text.text(f"Processing file {i + 1} of {len(uploaded_files)}: {uploaded_file.name}")
                        each_upload_data = read_file(uploaded_file)
                        if each_upload_data is not None:
                            total_rows = len(each_upload_data)
                            progress_bar = st.progress(0)
                            progress_text = "batch insert {} entity  in progress. Please wait.".format(
                                uploaded_file.name)
                            for j, item in enumerate(each_upload_data.itertuples(), 1):
                                question = str(item.question)
                                sql = str(item.sql)
                                VectorStore.add_sample(current_profile, question, sql)
                                progress = (j * 1.0) / total_rows
                                progress_bar.progress(progress, text=progress_text)
                            progress_bar.empty()
                        st.success("{uploaded_file} uploaded successfully!".format(uploaded_file=uploaded_file.name))
    else:
        st.info('Please select data profile in the left sidebar.')


if __name__ == '__main__':
    main()