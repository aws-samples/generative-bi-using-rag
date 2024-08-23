import streamlit as st
import sqlalchemy as db
from dotenv import load_dotenv
import logging
from nlq.business.connection import ConnectionManagement
from nlq.business.datasource.base import DataSourceBase
from nlq.business.datasource.factory import DataSourceFactory
from nlq.business.profile import ProfileManagement
from utils.navigation import make_sidebar

logger = logging.getLogger(__name__)


def new_profile_clicked():
    st.session_state.profile_page_mode = 'new'
    st.session_state.current_profile_name = None


@st.cache_data
def get_profile_by_name(profile_name):
    return ProfileManagement.get_profile_by_name(profile_name)


@st.cache_data
def get_all_profiles():
    return ProfileManagement.get_all_profiles()


@st.cache_data
def get_conn_config_by_name(conn_name):
    return ConnectionManagement.get_conn_config_by_name(conn_name)


@st.cache_data
def get_all_schemas_by_config(_conn_config, default_values):
    try:
        return ConnectionManagement.get_all_schemas_by_config(_conn_config)
    except Exception as e:
        logger.error(e)
        return default_values


# @st.cache_data
def get_table_name_by_config(_conn_config, schema_names, default_values):
    try:
        return ConnectionManagement.get_table_name_by_config(_conn_config, schema_names)
    except Exception as e:
        logger.error(e)
        return default_values


def show_delete_profile(profile_name):
    if st.button('Delete Profile'):
        st.session_state.update_profile = True
        ProfileManagement.delete_profile(profile_name)
        st.success(f"{profile_name} deleted successfully!")
        st.session_state.profile_page_mode = 'default'
        st.cache_data.clear()
        st.rerun()


def main():
    load_dotenv()
    logger.info('start data profile management')
    st.set_page_config(page_title="Data Profile Management", )
    make_sidebar()

    if "update_profile" not in st.session_state:
        st.session_state.update_profile = False

    if 'profile_page_mode' not in st.session_state:
        st.session_state['profile_page_mode'] = 'default'

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

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
        st.title("Data Profile Management")
        st.selectbox("My Data Profiles", get_all_profiles(),
                     index=None,
                     placeholder="Please select data profile...", key='current_profile_name')
        if st.session_state.current_profile_name:
            st.session_state.profile_page_mode = 'update'

        st.button('Create new profile...', on_click=new_profile_clicked)

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
                st.session_state.update_profile = True
                if not selected_tables:
                    st.error('Please select at least one table.')
                    return
                with st.spinner('Creating profile...'):
                    ProfileManagement.add_profile(profile_name, selected_conn_name, schema_names, selected_tables,
                                                  comments, conn_config.db_type)
                    st.success('Profile created.')
                    st.session_state.profile_page_mode = 'default'
                    table_definitions = ConnectionManagement.get_table_definition_by_config(conn_config, schema_names,
                                                                                            selected_tables)
                    st.write(table_definitions)
                    ProfileManagement.update_table_def(profile_name, table_definitions, merge_before_update=True)
                    # clear cache
                    st.cache_data.clear()

                # st.session_state.profile_page_mode = 'default'
    elif st.session_state.profile_page_mode == 'update' and st.session_state.current_profile_name is not None:
        st.subheader('Update Data Profile')
        current_profile = get_profile_by_name(st.session_state.current_profile_name)
        profile_name = st.text_input("Profile Name", value=current_profile.profile_name, disabled=True)
        selected_conn_name = st.text_input("Database Connection", value=current_profile.conn_name, disabled=True)
        conn_config = get_conn_config_by_name(selected_conn_name)
        if not conn_config:
            # if the connection record has been deleted, then allow user to delete the profile
            st.error('connection not found')
            show_delete_profile(profile_name)
            return
        schema_names = st.multiselect("Schema Name", get_all_schemas_by_config(conn_config, current_profile.schemas),
                                      default=current_profile.schemas)
        tables_from_db = get_table_name_by_config(conn_config, schema_names, current_profile.tables)
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
                                            "Examples:\n"
                                            "Your sample question 1\n"
                                            "Your sample question 2")

        st_enable_rls = False
        rls_config = None
        if DataSourceFactory.get_data_source(conn_config.db_type).support_row_level_security():
            st_enable_rls = st.checkbox("Enable Row Level Security", value=current_profile.enable_row_level_security,
                                        help=" Row level security: Replacing the generated SQL with user-aware "
                                             "filter. Support MySQL and Clickhouse.")
            rls_config = st.text_area("Row Level Security Filter using YAML",
                                      value=current_profile.row_level_security_config,
                                      placeholder="""tables:
  - table_name: table_a
    columns:
      - column_name: username
        column_value: $login_user.username""", disabled=not st_enable_rls, height=240)

        if st.button('Update Profile', type='primary'):
            st.session_state.update_profile = True
            if not selected_tables:
                st.error('Please select at least one table.')
                return
            with st.spinner('Updating profile...'):
                old_tables_info = ProfileManagement.get_profile_by_name(profile_name).tables_info
                if st_enable_rls:
                    has_validated = DataSourceBase.validate_row_level_security_config(rls_config)
                    if not has_validated:
                        st.error('Invalid row level security config.')
                        return
                ProfileManagement.update_profile(profile_name, selected_conn_name, schema_names, selected_tables,
                                                 comments, old_tables_info, conn_config.db_type, st_enable_rls,
                                                 rls_config)
                st.success('Profile updated. Please click "Fetch table definition" button to continue.')
                st.cache_data.clear()

        if st.button('Fetch table definition'):
            st.session_state.update_profile = True
            if not selected_tables:
                st.error('Please select at least one table.')
            with st.spinner('fetching...'):
                table_definitions = ConnectionManagement.get_table_definition_by_config(conn_config, schema_names,
                                                                                        selected_tables)
                st.write(table_definitions)
                ProfileManagement.update_table_def(profile_name, table_definitions, merge_before_update=True)
                st.session_state.profile_page_mode = 'default'
                st.cache_data.clear()

        show_delete_profile(profile_name)
    else:
        st.info('Please select connection in the left sidebar.')


if __name__ == '__main__':
    main()
