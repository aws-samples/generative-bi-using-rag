import time

import streamlit as st
from dotenv import load_dotenv
import logging
from nlq.business.profile import ProfileManagement
from nlq.business.vector_store import VectorStore
from utils.navigation import make_sidebar

logger = logging.getLogger(__name__)

def delete_entity_sample(profile_name, id):
    VectorStore.delete_entity_sample(profile_name, id)
    st.success(f'Sample {id} deleted.')


def main():
    load_dotenv()
    logger.info('start entity management')
    st.set_page_config(page_title="Entity Management", )
    make_sidebar()

    if 'profile_page_mode' not in st.session_state:
        st.session_state['index_mgt_mode'] = 'default'

    with st.sidebar:
        st.title("Entity Management")
        current_profile = st.selectbox("My Data Profiles", ProfileManagement.get_all_profiles(),
                                       index=None,
                                       placeholder="Please select data profile...", key='current_profile_name')

    tab_view, tab_add = st.tabs(['View Samples', 'Add New Sample'])
    if current_profile is not None:
        with tab_view:
            if current_profile is not None:
                for sample in VectorStore.get_all_entity_samples(current_profile):
                    # st.write(f"Sample: {sample}")
                    with st.expander(sample['entity']):
                        st.code(sample['comment'])
                        st.button('Delete ' + sample['id'], on_click=delete_entity_sample, args=[current_profile, sample['id']])

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
    else:
        st.info('Please select data profile in the left sidebar.')


if __name__ == '__main__':
    main()
