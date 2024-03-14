import streamlit as st
import sqlalchemy as db
from dotenv import load_dotenv
from loguru import logger
from nlq.business.connection import ConnectionManagement
from nlq.business.profile import ProfileManagement

def new_profile_clicked():
    st.session_state.profile_page_mode = 'new'
    st.session_state.current_profile_name = None


def main():
    load_dotenv()
    logger.info('start data profile management')
    st.set_page_config(page_title="Data Profile Management", )

    if 'profile_page_mode' not in st.session_state:
        st.session_state['profile_page_mode'] = 'default'

    with st.sidebar:
        st.title("Data Profile Management")
        st.selectbox("My Data Profiles", ProfileManagement.get_all_profiles(),
                     index=None,
                     placeholder="Please select data profile...", key='current_profile_name')
        if st.session_state.current_profile_name:
            st.session_state.profile_page_mode = 'update'

        st.button('新建...', on_click=new_profile_clicked)

    if st.session_state.profile_page_mode == 'new':
        st.subheader('Create New Data Profile')
        profile_name = st.text_input("Profile Name")
        selected_conn_name = st.selectbox("Database Connection", ConnectionManagement.get_all_connections(), index=None)

        if selected_conn_name:
            conn_config = ConnectionManagement.get_conn_config_by_name(selected_conn_name)
            schema_names = st.multiselect("Schema Name", ConnectionManagement.get_all_schemas_by_config(conn_config))
            tables_from_db = ConnectionManagement.get_table_name_by_config(conn_config, schema_names)
            print(tables_from_db)
            selected_tables = st.multiselect("Select tables included in this profile", tables_from_db)
            comments = st.text_input("Comments")

            if st.button('Create Profile', type='primary'):
                if not selected_tables:
                    st.error('Please select at least one table.')
                    return
                with st.spinner('Creating profile...'):
                    ProfileManagement.add_profile(profile_name, selected_conn_name, schema_names, selected_tables, comments)
                    st.success('Profile created.')
                    st.session_state.profile_page_mode = 'default'

                # st.session_state.profile_page_mode = 'default'
    elif st.session_state.profile_page_mode == 'update' and st.session_state.current_profile_name is not None:
        st.subheader('Update Data Profile')
        current_profile = ProfileManagement.get_profile_by_name(st.session_state.current_profile_name)
        profile_name = st.text_input("Profile Name", value=current_profile.profile_name, disabled=True)
        selected_conn_name = st.text_input("Database Connection", value=current_profile.conn_name, disabled=True)
        conn_config = ConnectionManagement.get_conn_config_by_name(selected_conn_name)
        schema_names = st.multiselect("Schema Name", ConnectionManagement.get_all_schemas_by_config(conn_config),
                                      default=current_profile.schemas)
        tables_from_db = ConnectionManagement.get_table_name_by_config(conn_config, schema_names)
        # make sure all tables defined in profile are existing in the table list of the current database
        intersection_tables = set(tables_from_db) & set(current_profile.tables)
        if len(intersection_tables) < len(current_profile.tables):
            st.warning(
                f"Some tables defined in this profile are not existing in the database.")
        if len(intersection_tables) == 0:
            intersection_tables = None
        selected_tables = st.multiselect("Select tables included in this profile", tables_from_db,
                                         default=intersection_tables)
        comments = st.text_area("Comments (add sample questions after Examples:, one question one line)",
                                value=current_profile.comments,
                                placeholder="Your comments for this data profile.\n"
                                "You can add sample questions after samples, one question one line.\n"
                                "Example:\n"
                                "Your sample question 1\n"
                                "Your sample question 2")

        if st.button('Update Profile', type='primary'):
            if not selected_tables:
                st.error('Please select at least one table.')
                return
            with st.spinner('Updating profile...'):
                old_tables_info = ProfileManagement.get_profile_by_name(profile_name).tables_info
                ProfileManagement.update_profile(profile_name, selected_conn_name, schema_names, selected_tables,
                                                 comments, old_tables_info)
                st.success('Profile updated. Please click "Fetch table definition" button to continue.')

        if st.button('Fetch table definition'):
            if not selected_tables:
                st.error('Please select at least one table.')
            with st.spinner('fetching...'):
                table_definitions = ConnectionManagement.get_table_definition_by_config(conn_config, schema_names,
                                                                                        selected_tables)
                st.write(table_definitions)
                ProfileManagement.update_table_def(profile_name, table_definitions, merge_before_update=True)
                st.session_state.profile_page_mode = 'default'

        if st.button('Delete Profile'):
            ProfileManagement.delete_profile(profile_name)
            st.success(f"{profile_name} deleted successfully!")
            st.session_state.profile_page_mode = 'default'

    else:
        # st.subheader("Data Profile Management")
        st.info('Please select connection in the left sidebar.')


if __name__ == '__main__':
    main()
