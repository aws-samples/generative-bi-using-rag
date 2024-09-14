import time
import streamlit as st
from dotenv import load_dotenv
import logging
from nlq.business.user_profile import UserProfileManagement
from nlq.business.profile import ProfileManagement
from utils.navigation import make_sidebar
import uuid


logger = logging.getLogger(__name__)

def generate_4_char_string():
    uuid_obj = uuid.uuid4()
    uuid_str = str(uuid_obj)
    short_str = uuid_str[:4]
    return short_str

def delete_user_map_entity(user_id):
    UserProfileManagement.delete_user_profile(user_id)
    st.success(f'User {user_id} profile map deleted.')


def select_all_in_view_tab(user_id):
    _tmp_map_value = {}
    for _,key in enumerate(st.session_state.all_map_value):
        if key == user_id:
            _tmp_map_value[key] = {}
            _tmp_map_value[key]['profile_name_list'] = ProfileManagement.get_all_profiles()
        else:
            _tmp_map_value[key] = st.session_state.all_map_value[key]
    st.session_state.all_map_value = _tmp_map_value

def clear_all_in_view_tab(user_id):
    _tmp_map_value = {}
    for _,key in enumerate(st.session_state.all_map_value):
        if key == user_id:
            _tmp_map_value[key] = {}
            _tmp_map_value[key]['profile_name_list'] = []
        else:
            _tmp_map_value[key] = st.session_state.all_map_value[key]
    st.session_state.all_map_value = _tmp_map_value

def main():
    load_dotenv()
    logger.info('start User Authorization Management')
    st.set_page_config(page_title="User Authorization", )
    make_sidebar()

    if "user_id_input_value" not in st.session_state:
        st.session_state.user_id_input_value = ""

    if "user_id_profile_map_value" not in st.session_state:
        st.session_state.user_id_profile_map_value = []

    if "all_map_value" not in st.session_state:
        st.session_state.all_map_value = {}

    if "changed_all_map_value" not in st.session_state:
        st.session_state.changed_all_map_value = False

    with st.sidebar:
        st.title("User Authorization Management")

    all_profiles = ProfileManagement.get_all_profiles()
    tab_view, tab_add = st.tabs(['View User Profile Map', 'Add New User Map'])
    with tab_view:
        user_profile_map = {}
        if not st.session_state.changed_all_map_value:
            all_map = UserProfileManagement.get_all_user_profiles_with_info()
            st.session_state.all_map_value = all_map
        else:
            all_map = st.session_state.all_map_value
        for i, user in enumerate(all_map):
            with st.expander(user):
                selected_profiles = st.multiselect('Select Data Profile', all_profiles, key=f'multiselect_{i}',default=st.session_state.all_map_value[user]['profile_name_list'])
                st.session_state.all_map_value[user]['profile_name_list'] = selected_profiles
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button('Select All',use_container_width=True,key=f'selectall_{i}'):
                        st.session_state.changed_all_map_value = True
                        select_all_in_view_tab(user)
                        st.rerun() 
                with col2:
                    if st.button('Clear', use_container_width=True,key=f'clear{i}'):
                        st.session_state.changed_all_map_value = True
                        clear_all_in_view_tab(user)
                        st.rerun()
                with col3:
                    if st.button('Delete', use_container_width=True,key=f'delete{i}'):
                        UserProfileManagement.delete_user_profile(user)
                        st.success(f'Remove User {user} access {selected_profiles} ')
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                with col4:
                    if st.button('Save', use_container_width=True,key=f'submit{i}'):
                        if len(user) > 0 and len(selected_profiles) > 0:
                            UserProfileManagement.update_user_profile(user, selected_profiles)
                            st.success(f'Authorized User {user} access {selected_profiles} ')
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error('Please input a valid user ID and select at least 1 profile.')
    with tab_add:
        new_user_id = st.text_input('User Id', key=f'new_user_id',value=st.session_state.user_id_input_value)
        st.session_state.user_id_input_value = new_user_id

        selected_profiles = st.multiselect('Select Data Profile', all_profiles, key=f'select_role',default=st.session_state.user_id_profile_map_value)
        st.session_state.user_id_profile_map_value = selected_profiles

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button('Select All',use_container_width=True,):
                st.session_state.user_id_profile_map_value = ProfileManagement.get_all_profiles()   
                st.rerun() 
        with col2:
            if st.button('Clear', use_container_width=True,):
                st.session_state.user_id_input_value = ""
                st.session_state.user_id_profile_map_value = []        
                st.rerun()
        with col3:
            if st.button('Submit', type='primary', use_container_width=True,):
                if len(new_user_id) > 0 and len(selected_profiles) > 0:
                    UserProfileManagement.update_user_profile(new_user_id, selected_profiles)
                    st.success(f'Authorized User {new_user_id} access {selected_profiles} ')
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error('Please input a valid user ID and select at least 1 profile.')

if __name__ == '__main__':
    main()
