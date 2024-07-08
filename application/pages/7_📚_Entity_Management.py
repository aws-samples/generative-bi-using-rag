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


def delete_entity_sample(profile_name, id):
    VectorStore.delete_entity_sample(profile_name, id)
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
    if "entity" in columns and "comment" in columns:
        return uploaded_data
    else:
        st.error(f"The columns need contains entity and comment")
        return None


def main():
    load_dotenv()
    logger.info('start entity management')
    st.set_page_config(page_title="Entity Management", )
    make_sidebar()

    if 'profile_page_mode' not in st.session_state:
        st.session_state['index_mgt_mode'] = 'default'

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

    with st.sidebar:
        st.title("Entity Management")
        all_profiles_list = ProfileManagement.get_all_profiles()
        if st.session_state.current_profile != "" and st.session_state.current_profile in all_profiles_list:
            profile_index = all_profiles_list.index(st.session_state.current_profile)
            current_profile = st.selectbox("My Data Profiles", all_profiles_list, index=profile_index)
        else:
            current_profile = st.selectbox("My Data Profiles", ProfileManagement.get_all_profiles(),
                                           index=None,
                                           placeholder="Please select data profile...", key='current_profile_name')

    tab_view, tab_add, tab_search, batch_insert = st.tabs(
        ['View Samples', 'Add New Sample', 'Sample Search', 'Batch Insert Samples'])
    if current_profile is not None:
        with tab_view:
            if current_profile is not None:
                st.write("The display page can show a maximum of 5000 pieces of data")
                for sample in VectorStore.get_all_entity_samples(current_profile):
                    # st.write(f"Sample: {sample}")
                    with st.expander(sample['entity']):
                        st.code(sample['comment'])
                        st.button('Delete ' + sample['id'], on_click=delete_entity_sample,
                                  args=[current_profile, sample['id']])

        with tab_add:
            if current_profile is not None:
                entity = st.text_input('Entity', key='index_question')
                comment = st.text_area('Comment', key='index_answer', height=300)

                if st.button('Submit', type='primary'):
                    if len(entity) > 0 and len(comment) > 0:
                        VectorStore.add_entity_sample(current_profile, entity, comment)
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
                        search_sample_result = VectorStore.search_sample(current_profile, retrieve_number,
                                                                         opensearch_info['ner_index'],
                                                                         entity_search)
                        for sample in search_sample_result:
                            sample_res = {'Score': sample['_score'],
                                          'Entity': sample['_source']['entity'],
                                          'Answer': sample['_source']['comment'].strip()}
                            st.code(sample_res)
                            st.button('Delete ' + sample['_id'], key=sample['_id'], on_click=delete_entity_sample,
                                      args=[current_profile, sample['_id']])

        with batch_insert:
            if current_profile is not None:
                st.write("This page support CSV or Excel files batch insert entity samples.")
                st.write("**The Column Name need contain 'entity' and 'comment'**")
                uploaded_files = st.file_uploader("Choose CSV or Excel files", accept_multiple_files=True,
                                              type=['csv', 'xls', 'xlsx'])
                if uploaded_files:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    for i, uploaded_file in enumerate(uploaded_files):
                        status_text.text(f"Processing file {i + 1} of {len(uploaded_files)}: {uploaded_file.name}")
                        each_upload_data = read_file(uploaded_file)
                        if each_upload_data is not None:
                            for index, item in each_upload_data.iterrows():
                                entity = str(item["entity"])
                                comment = str(item["comment"])
                                VectorStore.add_entity_sample(current_profile, entity, comment)
                        progress_bar.progress((i + 1) / len(uploaded_files))

                        st.success("{uploaded_file} uploaded successfully!".format(uploaded_file=uploaded_file.name))
                    progress_bar.empty()
    else:
        st.info('Please select data profile in the left sidebar.')


if __name__ == '__main__':
    main()
