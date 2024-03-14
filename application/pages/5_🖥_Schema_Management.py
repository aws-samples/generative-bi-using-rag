import streamlit as st
from dotenv import load_dotenv
from loguru import logger
from nlq.business.profile import ProfileManagement


def main():
    load_dotenv()
    logger.info('start schema management')
    st.set_page_config(page_title="Schema Management", )

    # if 'profile_page_mode' not in st.session_state:
    #     st.session_state['index_mgt_mode'] = 'default'

    with st.sidebar:
        st.title("Schema Management")
        current_profile = st.selectbox("My Data Profiles", ProfileManagement.get_all_profiles(),
                                       index=None,
                                       placeholder="Please select data profile...", key='current_profile_name')

    if current_profile is not None:
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
                tbl_annotataion = st.text_input('Table annotation', table_anno)

                if column_anno is not None:
                    col_annotation_text = column_anno
                else:
                # st.write(table_ddl)
                    print(table_ddl)
                    col_annotation_text = ''
                    start_flag = False
                    for li in table_ddl.split('\n'):
                        li = li.strip()
                        if li[0] == '(':
                            start_flag = True
                            continue
                        if li[0] == ')':
                            start_flag = False
                            continue
                        if start_flag:
                            li_parts = li.split(' ')
                            col_name = li_parts[0]
                            col_type = li_parts[1]
                            print(li_parts[2:])
                            col_comment = ' '.join(li_parts[2:]).replace(',', '').replace('--', '')
                            # print(li.split(' '))
                            col_annotation_text += f'- name: {col_name}, datatype: {col_type}, comment: {col_comment}\n'
                            col_annotation_text += '  annotataion: \n'

                col_annotation = st.text_area('Column annotation', col_annotation_text, height=500)

                if st.button('Save', type='primary'):
                    origin_tables_info = profile_detail.tables_info
                    origin_table_info = origin_tables_info[selected_table]
                    origin_table_info['tbl_a'] = tbl_annotataion
                    origin_table_info['col_a'] = col_annotation
                    ProfileManagement.update_table_def(current_profile, origin_tables_info)
                    st.success('saved.')


if __name__ == '__main__':
    main()
