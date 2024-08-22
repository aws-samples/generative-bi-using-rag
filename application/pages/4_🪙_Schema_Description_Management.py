import streamlit as st
from dotenv import load_dotenv
import logging
from nlq.business.profile import ProfileManagement
from utils.navigation import make_sidebar

logger = logging.getLogger(__name__)

def main():
    load_dotenv()
    logger.info('start schema management')
    st.set_page_config(page_title="Schema Management", )
    make_sidebar()

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
        st.title("Schema Management")
        all_profiles_list = st.session_state["profiles_list"]
        if st.session_state.current_profile != "" and st.session_state.current_profile in all_profiles_list:
            profile_index = all_profiles_list.index(st.session_state.current_profile)
            current_profile = st.selectbox("My Data Profiles", all_profiles_list, index=profile_index)
        else:
            current_profile = st.selectbox("My Data Profiles", all_profiles_list,
                                       index=None,
                                       placeholder="Please select data profile...", key='current_profile_name')

    if current_profile is not None:
        st.session_state['current_profile'] = current_profile
        profile_detail = ProfileManagement.get_profile_by_name(current_profile)

        selected_table = st.selectbox("Tables", profile_detail.tables, index=None, placeholder="Please select a table")
        if selected_table is not None:
            table_info = profile_detail.tables_info[selected_table]
            if table_info is not None:
                table_ddl = table_info['ddl']
                table_desc = table_info['description']
                table_anno = table_info.get('tbl_a')
                column_anno = table_info.get('col_a')

                st.caption(f'Table description: {table_desc}')
                tbl_annotation = st.text_input('Table annotation', table_anno)

                if column_anno is not None:
                    col_annotation_text = column_anno
                    col_annotation = st.text_area('Column annotation', col_annotation_text, height=500)
                else:
                    col_annotation = st.text_area('Column annotation', table_ddl, height=400, help='''e.g. CREATE TABLE employees (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique identifier for each employee',
    name VARCHAR(100) NOT NULL COMMENT 'Employee name', 
    position VARCHAR(50) NOT NULL COMMENT 'Job position, 2 possible values: 'Engineer', 'Manager',
    salary DECIMAL(10, 2) COMMENT 'Salary in USD, e.g., 1000.00',
    date DATE NOT NULL COMMENT 'Date of joining the company'
    ...
);
    ''')
                if st.button('Save', type='primary'):
                    st.session_state.update_profile = True
                    origin_tables_info = profile_detail.tables_info
                    origin_table_info = origin_tables_info[selected_table]
                    origin_table_info['tbl_a'] = tbl_annotation
                    origin_table_info['col_a'] = col_annotation
                    ProfileManagement.update_table_def(current_profile, origin_tables_info)
                    st.success('saved.')
    else:
        st.info('Please select data profile in the left sidebar.')

if __name__ == '__main__':
    main()
