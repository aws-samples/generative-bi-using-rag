import json
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import logging
import random

from api.service import user_feedback_downvote
from nlq.business.connection import ConnectionManagement
from nlq.business.nlq_chain import NLQChain
from nlq.business.profile import ProfileManagement
from nlq.business.vector_store import VectorStore
from nlq.core.chat_context import ProcessingContext
from nlq.core.state import QueryState
from nlq.core.state_machine import QueryStateMachine
from utils.domain import SearchTextSqlResult
from utils.llm import get_query_intent, generate_suggested_question, get_agent_cot_task, data_analyse_tool, \
    knowledge_search, text_to_sql, get_query_rewrite
from utils.navigation import make_sidebar
from utils.apis import get_sql_result_tool
from utils.prompts.generate_prompt import prompt_map_dict
from utils.opensearch import get_retrieve_opensearch
from utils.text_search import agent_text_search
from utils.tool import get_generated_sql
from utils.env_var import opensearch_info

logger = logging.getLogger(__name__)


def sample_question_clicked(sample):
    """Update the selected_sample variable with the text of the clicked button"""
    st.session_state['selected_sample'] = sample


def upvote_clicked(question, sql):
    """
    add upvote button to opensearch
    :param question: user question
    :param sql: true SQL
    :param env_vars:
    :return:
    """
    current_profile = st.session_state.current_profile
    VectorStore.add_sample(current_profile, question, sql)
    logger.info(f'up voted "{question}" with sql "{sql}"')


def upvote_agent_clicked(question, comment):
    # HACK: configurable opensearch endpoint

    current_profile = st.session_state.current_profile
    VectorStore.add_agent_cot_sample(current_profile, question, str(comment))
    logger.info(f'up voted "{question}" with sql "{comment}"')


def downvote_clicked(question, comment):
    current_profile = st.session_state.current_profile
    user_id = "admin"
    session_id = "-1"
    query = question
    query_intent = "normal_search"
    query_answer = str(comment)
    user_feedback_downvote(current_profile, user_id, session_id, query, query_intent, query_answer)


def clean_st_history(selected_profile):
    st.session_state.messages[selected_profile] = []
    st.session_state.query_rewrite_history[selected_profile] = []


def set_vision_change():
    st.session_state.vision_change = True


def get_user_history(selected_profile: str):
    """
    get user history for selected profile
    :param selected_profile:
    :return: history for selected profile list type
    """
    history_list = st.session_state.query_rewrite_history[selected_profile]
    history_query = []
    for messages in history_list:
        if messages["content"] is not None:
            history_query.append(messages["role"] + ":" + messages["content"])
    return history_query


def do_visualize_results():
    sql_query_result = st.session_state.current_sql_result
    if sql_query_result is not None:
        # Auto-detect columns
        available_columns = sql_query_result.columns.tolist()

        # Initialize session state for x_column and y_column if not already present
        if 'x_column' not in st.session_state or st.session_state.x_column is None:
            st.session_state.x_column = available_columns[0] if available_columns else None
        if 'y_column' not in st.session_state or st.session_state.x_column is None:
            st.session_state.y_column = available_columns[0] if available_columns else None

        # Layout configuration
        col1, col2, col3 = st.columns([1, 1, 2])

        # Chart type selection
        chart_type = col1.selectbox('Choose the chart type', ['Table', 'Bar', 'Line', 'Pie'],
                                    on_change=set_vision_change)

        if chart_type != 'Table':
            # X-axis and Y-axis selection
            st.session_state.x_column = col2.selectbox('Choose x-axis column', available_columns,
                                                       on_change=set_vision_change,
                                                       index=available_columns.index(
                                                           st.session_state.x_column) if st.session_state.x_column in available_columns else 0)
            st.session_state.y_column = col3.selectbox('Choose y-axis column', available_columns,
                                                       on_change=set_vision_change,
                                                       index=available_columns.index(
                                                           st.session_state.y_column) if st.session_state.y_column in available_columns else 0)

        # Visualization
        if chart_type == 'Table':
            st.dataframe(sql_query_result, hide_index=True)
        elif chart_type == 'Bar':
            st.plotly_chart(px.bar(sql_query_result, x=st.session_state.x_column, y=st.session_state.y_column))
        elif chart_type == 'Line':
            st.plotly_chart(px.line(sql_query_result, x=st.session_state.x_column, y=st.session_state.y_column))
        elif chart_type == 'Pie':
            st.plotly_chart(px.pie(sql_query_result, names=st.session_state.x_column, values=st.session_state.y_column))
    else:
        st.markdown('No visualization generated.')


def recurrent_display(messages, i):
    # hacking way of displaying messages, since the chat_message does not support multiple messages outside of "with" statement
    current_role = messages[i]["role"]
    message = messages[i]
    if message["type"] == "pandas":
        if isinstance(message["content"], pd.DataFrame):
            st.dataframe(message["content"], hide_index=True)
        elif isinstance(message["content"], list):
            for each_content in message["content"]:
                st.write(each_content["query"])
                st.dataframe(pd.read_json(each_content["data_result"], orient='records'), hide_index=True)
    elif message["type"] == "text":
        st.markdown(message["content"])
    elif message["type"] == "error":
        st.error(message["content"])
    elif message["type"] == "sql":
        with st.expander("The Generate SQL"):
            st.code(message["content"], language="sql")
    return i


def main():
    load_dotenv()

    st.set_page_config(page_title="Demo", layout="wide")
    make_sidebar()

    # Title and Description
    st.subheader('Generative BI Playground')

    demo_profile_suffix = '(demo)'
    # Initialize or set up state variables
    if 'profiles' not in st.session_state:
        # get all user defined profiles with info (db_url, conn_name, tables_info, hints, search_samples)
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        # all_profiles.update(demo_profile)
        st.session_state['profiles'] = all_profiles
    else:
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        st.session_state['profiles'] = all_profiles

    if "vision_change" not in st.session_state:
        st.session_state["vision_change"] = False

    if 'selected_sample' not in st.session_state:
        st.session_state['selected_sample'] = ''

    if 'ask_replay' not in st.session_state:
        st.session_state.ask_replay = False

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

    if 'current_model_id' not in st.session_state:
        st.session_state['current_model_id'] = ''

    if 'config_data_with_analyse' not in st.session_state:
        st.session_state['config_data_with_analyse'] = False

    if 'nlq_chain' not in st.session_state:
        st.session_state['nlq_chain'] = None

    if "messages" not in st.session_state:
        st.session_state.messages = {}

    if "query_rewrite_history" not in st.session_state:
        st.session_state.query_rewrite_history = {}

    if "current_sql_result" not in st.session_state:
        st.session_state.current_sql_result = {}

    model_ids = ['anthropic.claude-3-sonnet-20240229-v1:0', 'anthropic.claude-3-5-sonnet-20240620-v1:0',
                 'anthropic.claude-3-opus-20240229-v1:0',
                 'anthropic.claude-3-haiku-20240307-v1:0', 'mistral.mixtral-8x7b-instruct-v0:1',
                 'meta.llama3-70b-instruct-v1:0']

    session_state_list = list(st.session_state.get('profiles', {}).keys())

    hava_session_state_flag = False
    if len(session_state_list) > 0:
        hava_session_state_flag = True

    with st.sidebar:
        st.title('Setting')
        # The default option can be the first one in the profiles dictionary, if exists
        session_state_list = list(st.session_state.get('profiles', {}).keys())
        if st.session_state.current_profile != "":
            if st.session_state.current_profile in session_state_list:
                profile_index = session_state_list.index(st.session_state.current_profile)
                selected_profile = st.selectbox("Data Profile", session_state_list, index=profile_index)
            else:
                selected_profile = st.selectbox("Data Profile", session_state_list)
        else:
            selected_profile = st.selectbox("Data Profile", session_state_list)
        if selected_profile != st.session_state.current_profile:
            # clear session state
            st.session_state.selected_sample = ''
            st.session_state.current_profile = selected_profile
            if selected_profile not in st.session_state.messages:
                st.session_state.messages[selected_profile] = []
            if selected_profile not in st.session_state.query_rewrite_history:
                st.session_state.query_rewrite_history[selected_profile] = []
            st.session_state.nlq_chain = NLQChain(selected_profile)
        else:
            if selected_profile not in st.session_state.messages:
                st.session_state.messages[selected_profile] = []
            if selected_profile not in st.session_state.query_rewrite_history:
                st.session_state.query_rewrite_history[selected_profile] = []
            st.session_state.nlq_chain = NLQChain(selected_profile)

        if st.session_state.current_model_id != "" and st.session_state.current_model_id in model_ids:
            model_index = model_ids.index(st.session_state.current_model_id)
            model_type = st.selectbox("Choose your model", model_ids, index=model_index)
        else:
            model_type = st.selectbox("Choose your model", model_ids)

        use_rag_flag = st.checkbox("Using RAG from Q/A Embedding", True)
        visualize_results_flag = st.checkbox("Visualize Results", True)
        intent_ner_recognition_flag = st.checkbox("Intent NER", True)
        agent_cot_flag = st.checkbox("Agent COT", True)
        explain_gen_process_flag = st.checkbox("Explain Generation Process", True)
        data_with_analyse = st.checkbox("Answer With Insights", False)
        gen_suggested_question_flag = st.checkbox("Generate Suggested Questions", False)
        auto_correction_flag = st.checkbox("Auto Correcting SQL", True)
        context_window = st.slider("Multiple Rounds of Context Window", 0, 10, 5)

        clean_history = st.button("clean history", on_click=clean_st_history, args=[selected_profile])

    st.chat_message("assistant").write(
        f"I'm the Generative BI assistant. Please **ask a question** or **select a sample question** below to start.")

    if not hava_session_state_flag:
        st.info("You should first create a database connection and then create a data profile")
        return

    # Display sample questions
    comments = st.session_state.profiles[selected_profile]['comments']
    comments_questions = []
    if len(comments.split("Examples:")) > 1:
        comments_questions_txt = comments.split("Examples:")[1]
        comments_questions = [i for i in comments_questions_txt.split("\n") if i != '']

    search_samples = st.session_state.profiles[selected_profile]['search_samples']
    search_samples = search_samples + comments_questions
    question_column_number = 3
    search_sample_columns = st.columns(question_column_number)

    for i, sample in enumerate(search_samples):
        i = i % question_column_number
        search_sample_columns[i].button(sample, use_container_width=True, on_click=sample_question_clicked,
                                        args=[sample])

    current_nlq_chain = st.session_state.nlq_chain

    # Display chat messages from history
    logger.info(f'{st.session_state.messages}')
    if selected_profile in st.session_state.messages:
        current_role = ""
        new_index = 0
        for i in range(len(st.session_state.messages[selected_profile])):
            print('!!!!!')
            print(i, new_index)
            # if i - 1 < new_index:
            #     continue
            with st.chat_message(st.session_state.messages[selected_profile][i]["role"]):
                new_index = recurrent_display(st.session_state.messages[selected_profile], i)

    text_placeholder = "Type your query here..."

    search_box = st.chat_input(placeholder=text_placeholder)
    if st.session_state['selected_sample'] != "":
        search_box = st.session_state['selected_sample']
        st.session_state['selected_sample'] = ""

    database_profile = st.session_state.profiles[selected_profile]
    with st.spinner('Connecting to database...'):
        # fix db url is Empty
        if database_profile['db_url'] == '':
            conn_name = database_profile['conn_name']
            db_url = ConnectionManagement.get_db_url_by_name(conn_name)
            database_profile['db_url'] = db_url
            database_profile['db_type'] = ConnectionManagement.get_db_type_by_name(conn_name)
    prompt_map = database_profile['prompt_map']

    st.session_state.ask_replay = False

    # add select box for which model to use
    if search_box != "Type your query here..." or st.session_state.vision_change:
        if search_box is not None and len(search_box) > 0:
            st.session_state.current_sql_result = None
            with st.chat_message("user"):
                current_nlq_chain.set_question(search_box)
                st.session_state.messages[selected_profile].append(
                    {"role": "user", "content": search_box, "type": "text"})
                st.session_state.query_rewrite_history[selected_profile].append(
                    {"role": "user", "content": search_box})
                st.markdown(current_nlq_chain.get_question())
            user_query_history = get_user_history(selected_profile)
            with (st.chat_message("assistant")):
                processing_context = ProcessingContext(
                    search_box=search_box,
                    query_rewrite="",
                    session_id="",
                    user_id="",
                    selected_profile=selected_profile,
                    database_profile=database_profile,
                    model_type=model_type,
                    use_rag_flag=use_rag_flag,
                    intent_ner_recognition_flag=intent_ner_recognition_flag,
                    agent_cot_flag=agent_cot_flag,
                    explain_gen_process_flag=explain_gen_process_flag,
                    visualize_results_flag=visualize_results_flag,
                    data_with_analyse=data_with_analyse,
                    gen_suggested_question_flag=gen_suggested_question_flag,
                    auto_correction_flag=auto_correction_flag,
                    context_window=context_window,
                    entity_same_name_select={},
                    user_query_history=user_query_history,
                    opensearch_info=opensearch_info,
                    previous_state="INITIAL")
                state_machine = QueryStateMachine(processing_context)
                while state_machine.get_state() != QueryState.COMPLETE and state_machine.get_state() != QueryState.ERROR:
                    if state_machine.get_state() == QueryState.INITIAL:
                        with st.status("Query Context Understanding") as status_text:
                            state_machine.handle_initial()
                            st.write(state_machine.get_answer().query_rewrite)
                        status_text.update(label=f"Query Context Rewrite Completed", state="complete", expanded=False)
                        if state_machine.get_answer().query_intent == "ask_in_reply":
                            st.session_state.query_rewrite_history[selected_profile].append(
                                {"role": "assistant", "content": state_machine.get_answer().query_rewrite})
                            st.session_state.messages[selected_profile].append(
                                {"role": "assistant", "content": state_machine.get_answer().query_rewrite,
                                 "type": "text"})
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
                            sql = state_machine.intent_search_result["sql"]
                            st.code(sql, language="sql")
                            feedback = st.columns(2)
                            feedback[0].button('👍 Upvote (save as embedding for retrieval)', type='secondary',
                                               use_container_width=True,
                                               on_click=upvote_clicked,
                                               args=[search_box,
                                                     sql])
                            if feedback[1].button('👎 Downvote', type='secondary', use_container_width=True):
                                # do something here
                                pass
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
                    elif state_machine.state == QueryState.EXECUTE_QUERY:
                        state_machine.handle_execute_query()
                    elif state_machine.get_state() == QueryState.ANALYZE_DATA:
                        state_machine.handle_analyze_data()
                    else:
                        state_machine.state = QueryState.ERROR
                if state_machine.get_state() == QueryState.COMPLETE:
                    if state_machine.get_answer().query_intent == "normal_search":
                        st.session_state.messages[selected_profile].append(
                            {"role": "assistant", "content": state_machine.intent_search_result["sql"], "type": "sql"})
                        if state_machine.intent_search_result["sql_execute_result"]["status_code"] == 200:
                            st.session_state.current_sql_result = \
                            state_machine.intent_search_result["sql_execute_result"]["data"]
                            do_visualize_results()
        else:
            do_visualize_results()


if __name__ == '__main__':
    main()
