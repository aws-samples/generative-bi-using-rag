import time

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from nlq.business.profile import ProfileManagement
from nlq.business.vector_store import VectorStore
from utils.logging import getLogger
from utils.navigation import make_sidebar
from utils.env_var import opensearch_info
from nlq.business.connection import ConnectionManagement
from nlq.core.chat_context import ProcessingContext
from nlq.core.state import QueryState
from nlq.core.state_machine import QueryStateMachine

logger = getLogger()


def test_all_sample(selected_profile, model_type):
    logger.info(f'profile_name={selected_profile}')
    result = []
    # Initialize or set up state variables
    if 'profiles' not in st.session_state:
        # get all user defined profiles with info (db_url, conn_name, tables_info, hints, search_samples)
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        st.session_state['profiles'] = all_profiles
    else:
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        st.session_state['profiles'] = all_profiles

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

    if 'current_model_id' not in st.session_state:
        st.session_state['current_model_id'] = ''

    if "messages" not in st.session_state:
        st.session_state.messages = {selected_profile: []}

    all_samples = VectorStore.get_all_samples(selected_profile)
    total_rows = len(all_samples)
    progress_bar = st.progress(0)
    for i, sample in list(enumerate(all_samples)):
        status_text = st.empty()
        status_text.text(f"Processing {i + 1} of {total_rows} - {[sample['text']]} ")
        progress = (i + 1) / total_rows
        progress_bar.progress(progress)

        logger.info("===>> \n\n")

        logger.info(f'session:{st.session_state}')

        database_profile = st.session_state.profiles[selected_profile]
        with st.spinner('Connecting to database...'):
            # fix db url is Empty
            if database_profile['db_url'] == '':
                conn_name = database_profile['conn_name']
                db_url = ConnectionManagement.get_db_url_by_name(conn_name)
                database_profile['db_url'] = db_url
                database_profile['db_type'] = ConnectionManagement.get_db_type_by_name(conn_name)

        logger.info(f'database_profile={database_profile}')

        processing_context = ProcessingContext(
            search_box=sample['text'],
            query_rewrite="",
            session_id="",
            user_id=st.session_state['auth_username'],
            username=st.session_state['username'],
            selected_profile=selected_profile,
            database_profile=database_profile,
            model_type=model_type,
            use_rag_flag=True,
            intent_ner_recognition_flag=True,
            agent_cot_flag=False,
            explain_gen_process_flag=False,
            visualize_results_flag=True,
            data_with_analyse=False,
            gen_suggested_question_flag=False,
            auto_correction_flag=True,
            context_window=0,
            entity_same_name_select={},
            user_query_history=[],
            opensearch_info=opensearch_info,
            previous_state="INITIAL"
        )
        state_machine = QueryStateMachine(processing_context)
        while state_machine.get_state() != QueryState.COMPLETE and state_machine.get_state() != QueryState.ERROR:
            if state_machine.get_state() == QueryState.INITIAL:
                with st.status("Query Context Understanding") as status_text:
                    state_machine.handle_initial()
                    st.write(state_machine.get_answer().query_rewrite)
            elif state_machine.get_state() == QueryState.REJECT_INTENT:
                state_machine.handle_reject_intent()
                st.write("Your query statement is currently not supported by the system")
            elif state_machine.get_state() == QueryState.KNOWLEDGE_SEARCH:
                state_machine.handle_knowledge_search()
                st.write(state_machine.get_answer().knowledge_search_result.knowledge_response)
                st.session_state.messages[selected_profile].append(
                    {"role": "assistant",
                     "content": state_machine.get_answer().knowledge_search_result.knowledge_response,
                     "type": "text"})
            elif state_machine.get_state() == QueryState.ENTITY_RETRIEVAL:
                with st.status("Performing Entity retrieval...") as status_text:
                    state_machine.handle_entity_retrieval()
                    examples = []
                    for example in state_machine.normal_search_entity_slot:
                        examples.append({'Score': example['_score'],
                                         'Question': example['_source']['entity'],
                                         'Answer': example['_source']['comment'].strip()})
                    st.write(examples)
                    status_text.update(
                        label=f"Entity Retrieval Completed: {len(state_machine.normal_search_entity_slot)} entities retrieved",
                        state="complete", expanded=False)
            elif state_machine.get_state() == QueryState.QA_RETRIEVAL:
                state_machine.handle_qa_retrieval()
                with st.status("Performing QA retrieval...") as status_text:
                    examples = []
                    for example in state_machine.normal_search_qa_retrival:
                        examples.append({'Score': example['_score'],
                                         'Question': example['_source']['text'],
                                         'Answer': example['_source']['sql'].strip()})
                    st.write(examples)
                    status_text.update(
                        label=f"QA Retrieval Completed: {len(state_machine.normal_search_qa_retrival)} entities retrieved",
                        state="complete", expanded=False)
            elif state_machine.get_state() == QueryState.SQL_GENERATION:
                with st.status("Generating SQL... ") as status_text:
                    state_machine.handle_sql_generation()
                    sql = state_machine.get_answer().sql_search_result.sql
                    st.code(sql, language="sql")
                    st.session_state.messages[selected_profile].append(
                        {"role": "assistant", "content": sql, "type": "sql"})
                    status_text.update(
                        label=f"Generating SQL Done",
                        state="complete", expanded=True)

            elif state_machine.get_state() == QueryState.INTENT_RECOGNITION:
                with st.status("Performing intent recognition...") as status_text:
                    state_machine.handle_intent_recognition()
                    intent = state_machine.intent_response.get("intent", "normal_search")
                    st.write(state_machine.intent_response)
                status_text.update(label=f"Intent Recognition Completed: This is a **{intent}** question",
                                   state="complete", expanded=False)
            elif state_machine.get_state() == QueryState.EXECUTE_QUERY:
                state_machine.handle_execute_query()
            elif state_machine.get_state() == QueryState.ASK_ENTITY_SELECT:
                state_machine.handle_entity_selection()
                if state_machine.get_answer().query_intent == "entity_select":
                    st.session_state.previous_state[selected_profile] = "ASK_ENTITY_SELECT"
                    st.markdown(state_machine.get_answer().ask_entity_select.entity_select)
                    st.session_state.query_rewrite_history[selected_profile].append(
                        {"role": "assistant", "content": state_machine.get_answer().ask_entity_select.entity_select})
                    st.session_state.messages[selected_profile].append(
                        {"role": "assistant", "content": state_machine.get_answer().ask_entity_select.entity_select,
                         "type": "text"})
            elif state_machine.get_state() == QueryState.AGENT_TASK:
                with st.status("Agent Cot retrieval...") as status_text:
                    state_machine.handle_agent_task()
                    agent_examples = []
                    for example in state_machine.agent_cot_retrieve:
                        agent_examples.append({'Score': example['_score'],
                                               'Question': example['_source']['query'],
                                               'Answer': example['_source']['comment'].strip()})
                    st.write(agent_examples)
                status_text.update(label=f"Agent Cot Retrieval Completed",
                                   state="complete", expanded=False)
                with st.status("Agent Task split...") as status_text:
                    st.write(state_machine.agent_task_split)
                status_text.update(label=f"Agent Task Split Completed",
                                   state="complete", expanded=False)
            elif state_machine.get_state() == QueryState.AGENT_SEARCH:
                with st.status("Multiple SQL generated...") as status_text:
                    state_machine.handle_agent_sql_generation()
                    st.write(state_machine.agent_search_result)
                status_text.update(label=f"Multiple SQL Generated Completed",
                                   state="complete", expanded=False)
            elif state_machine.get_state() == QueryState.AGENT_DATA_SUMMARY:
                with st.spinner('Generating data summarize...'):
                    state_machine.handle_agent_analyze_data()
                    for i in range(len(state_machine.agent_valid_data)):
                        st.write(state_machine.agent_valid_data[i]["query"])
                        st.dataframe(pd.read_json(state_machine.agent_valid_data[i]["data_result"],
                                                  orient='records'), hide_index=True)
                    st.session_state.messages[selected_profile].append(
                        {"role": "assistant", "content": state_machine.agent_valid_data, "type": "pandas"})

                    st.markdown(state_machine.get_answer().agent_search_result.agent_summary)
                    st.session_state.messages[selected_profile].append(
                        {"role": "assistant", "content": state_machine.get_answer().agent_search_result.agent_summary,
                         "type": "text"})
            else:
                state_machine.state = QueryState.ERROR

        index = i + 1
        inputQuestion = sample['text']
        sampleSQL = sample['sql']
        testResult = state_machine.intent_search_result["sql_execute_result"]

        if state_machine.get_state() == QueryState.COMPLETE:
            if state_machine.get_answer().query_intent == "normal_search":
                if state_machine.intent_search_result["sql_execute_result"]["status_code"] == 200:
                    result.append([
                        i,
                        sample['text'],
                        sample['sql'],
                        state_machine.intent_search_result["sql_execute_result"]
                    ])
                    st.session_state.current_sql_result = \
                        state_machine.intent_search_result["sql_execute_result"]["data"]
                    # do_visualize_results()

        result.append({
            'index': index,
            'inputQuestion': inputQuestion,
            'sampleSQL': sampleSQL,
            'testResult': testResult

        })
    return result


@st.dialog("Modify the SQL value")
def edit_value(profile, entity_item, entity_id):
    text_value = entity_item["text"]
    sql_value = entity_item["sql"]
    text = st.text_input('Question', value=text_value)
    sql = st.text_area('Answer(SQL)', value=sql_value, height=300)
    left_button, right_button = st.columns([1, 2])
    with right_button:
        if st.button("Submit"):
            if text == text_value:
                VectorStore.add_sample(profile, text, sql)
            else:
                VectorStore.delete_sample(profile, entity_id)
                VectorStore.add_sample(profile, text, sql)
                st.success("Sample updated successfully!")
                with st.spinner('Update Index ...'):
                    time.sleep(2)
                st.session_state["sql_sample_search"][profile] = VectorStore.get_all_samples(profile)
                st.rerun()
    with left_button:
        if st.button("Cancel"):
            st.rerun()


def delete_sample(profile_name, id):
    VectorStore.delete_sample(profile_name, id)
    new_value = []
    for item in st.session_state["sql_sample_search"][profile_name]:
        if item["id"] != id:
            new_value.append(item)
    st.session_state["sql_sample_search"][profile_name] = new_value
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

    if "sql_sample_search" not in st.session_state:
        st.session_state["sql_sample_search"] = {}

    if 'sql_refresh_view' not in st.session_state:
        st.session_state['sql_refresh_view'] = False

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

        if current_profile not in st.session_state["sql_sample_search"]:
            st.session_state["sql_sample_search"][current_profile] = None

    if current_profile is not None:
        if st.session_state.sql_refresh_view or st.session_state["sql_sample_search"][current_profile] is None:
            st.session_state["sql_sample_search"][current_profile] = VectorStore.get_all_samples(current_profile)
            st.session_state.sql_refresh_view = False

    tab_view, tab_add, tab_search, batch_insert, reg_testing = st.tabs(
        ['View Samples', 'Add New Sample', 'Sample Search', 'Batch Insert Samples', 'Regression Test'])

    if current_profile is not None:
        st.session_state['current_profile'] = current_profile
        with tab_view:
            if current_profile is not None:
                st.write("The display page can show a maximum of 5000 pieces of data")
                for sample in st.session_state["sql_sample_search"][current_profile]:
                    with st.expander(sample['text']):
                        st.code(sample['sql'])
                        st.button('Edit ' + sample['id'], on_click=edit_value,
                                  args=[current_profile, sample, sample['id']])
                        st.button('Delete ' + sample['id'], on_click=delete_sample,
                                  args=[current_profile, sample['id']])

        with tab_add:
            with st.form(key='sql_add_form'):
                question = st.text_input('Question', key='index_question')
                answer = st.text_area('Answer(SQL)', key='index_answer', height=300)

                if st.form_submit_button('Add SQL Info', type='primary'):
                    if len(question) > 0 and len(answer) > 0:
                        VectorStore.add_sample(current_profile, question, answer)
                        st.success('Sample added')
                        st.success('Update Index')
                        with st.spinner('Update Index ...'):
                            time.sleep(2)
                        st.session_state["sql_sample_search"][current_profile] = VectorStore.get_all_samples(current_profile)
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

        with reg_testing:
            if current_profile is not None:
                total_sample_count = len(VectorStore.get_all_samples(current_profile))
                st.write(f"Total [{total_sample_count}] samples to be tested !")
                model_ids = ['anthropic.claude-3-sonnet-20240229-v1:0', 'anthropic.claude-3-5-sonnet-20240620-v1:0',
                             'anthropic.claude-3-opus-20240229-v1:0',
                             'anthropic.claude-3-haiku-20240307-v1:0', 'mistral.mixtral-8x7b-instruct-v0:1',
                             'meta.llama3-70b-instruct-v1:0']
                if 'current_model_id' in st.session_state.keys() and st.session_state.current_model_id != "" and st.session_state.current_model_id in model_ids:
                    model_index = model_ids.index(st.session_state.current_model_id)
                    model_type = st.selectbox("Choose your model", model_ids, index=model_index)
                else:
                    model_type = st.selectbox("Choose your model", model_ids)

                if st.button('Test All', type='primary'):
                    if total_sample_count > 0:
                        test_result = test_all_sample(current_profile, model_type)
                        st.write('Regression Testing Result:')
                        st.write(test_result)
                    st.success('Testing Completed')

    else:
        st.info('Please select data profile in the left sidebar.')


if __name__ == '__main__':
    main()
