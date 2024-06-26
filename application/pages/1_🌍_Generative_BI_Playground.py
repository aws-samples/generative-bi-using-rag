import json
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import logging
import random

from nlq.business.connection import ConnectionManagement
from nlq.business.nlq_chain import NLQChain
from nlq.business.profile import ProfileManagement
from nlq.business.vector_store import VectorStore
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


def clean_st_history(selected_profile):
    st.session_state.messages[selected_profile] = []


def get_user_history(selected_profile: str):
    """
    get user history for selected profile
    :param selected_profile:
    :return: history for selected profile list type
    """
    history_list = st.session_state.messages[selected_profile]
    history_query = []
    for messages in history_list:
        current_role = messages["role"]
        if current_role == "user":
            history_query.append(messages["content"])
    return history_query


def do_visualize_results(nlq_chain, sql_result):
    sql_query_result = sql_result
    if sql_query_result is not None:
        nlq_chain.set_visualization_config_change(False)
        # Auto-detect columns
        visualize_config_columns = st.columns(3)

        available_columns = sql_query_result.columns

        # hacky way to get around the issue of selectbox not updating when the options change
        chart_type = visualize_config_columns[0].selectbox('Choose the chart type',
                                                           ['Table', 'Bar', 'Line', 'Pie'],
                                                           on_change=nlq_chain.set_visualization_config_change
                                                           )
        if chart_type != 'Table':
            x_column = visualize_config_columns[1].selectbox(f'Choose x-axis column', available_columns,
                                                             on_change=nlq_chain.set_visualization_config_change,
                                                             key=random.randint(0, 10000)
                                                             )
            y_column = visualize_config_columns[2].selectbox('Choose y-axis column',
                                                             reversed(available_columns.to_list()),
                                                             on_change=nlq_chain.set_visualization_config_change,
                                                             key=random.randint(0, 10000)
                                                             )
        if chart_type == 'Table':
            st.dataframe(sql_query_result, hide_index=True)
        elif chart_type == 'Bar':
            st.plotly_chart(px.bar(sql_query_result, x=x_column, y=y_column))
        elif chart_type == 'Line':
            st.plotly_chart(px.line(sql_query_result, x=x_column, y=y_column))
        elif chart_type == 'Pie':
            st.plotly_chart(px.pie(sql_query_result, names=x_column, values=y_column))
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


def normal_text_search_streamlit(search_box, model_type, database_profile, entity_slot, opensearch_info, selected_profile,
                                 use_rag,
                                 model_provider=None):
    entity_slot_retrieve = []
    retrieve_result = []
    response = ""
    sql = ""
    search_result = SearchTextSqlResult(search_query=search_box, entity_slot_retrieve=entity_slot_retrieve,
                                        retrieve_result=retrieve_result, response=response, sql=sql)
    try:
        if database_profile['db_url'] == '':
            conn_name = database_profile['conn_name']
            db_url = ConnectionManagement.get_db_url_by_name(conn_name)
            database_profile['db_url'] = db_url
            database_profile['db_type'] = ConnectionManagement.get_db_type_by_name(conn_name)

        with st.status("Performing Entity retrieval...") as status_text:
            if len(entity_slot) > 0 and use_rag:
                for each_entity in entity_slot:
                    entity_retrieve = get_retrieve_opensearch(opensearch_info, each_entity, "ner",
                                                              selected_profile, 1, 0.7)
                    if len(entity_retrieve) > 0:
                        entity_slot_retrieve.extend(entity_retrieve)
            examples = []
            for example in entity_slot_retrieve:
                examples.append({'Score': example['_score'],
                                 'Question': example['_source']['entity'],
                                 'Answer': example['_source']['comment'].strip()})
            st.write(examples)
            status_text.update(
                label=f"Entity Retrieval Completed: {len(entity_slot_retrieve)} entities retrieved",
                state="complete", expanded=False)

        with st.status("Performing QA retrieval...") as status_text:
            if use_rag:
                retrieve_result = get_retrieve_opensearch(opensearch_info, search_box, "query",
                                                          selected_profile, 3, 0.5)
                examples = []
                for example in retrieve_result:
                    examples.append({'Score': example['_score'],
                                     'Question': example['_source']['text'],
                                     'Answer': example['_source']['sql'].strip()})
                st.write(examples)
                status_text.update(
                    label=f"QA Retrieval Completed: {len(retrieve_result)} entities retrieved",
                    state="complete", expanded=False)

        with st.status("Generating SQL... ") as status_text:
            response = text_to_sql(database_profile['tables_info'],
                                   database_profile['hints'],
                                   database_profile['prompt_map'],
                                   search_box,
                                   model_id=model_type,
                                   sql_examples=retrieve_result,
                                   ner_example=entity_slot_retrieve,
                                   dialect=database_profile['db_type'],
                                   model_provider=model_provider)

            sql = get_generated_sql(response)

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

            search_result = SearchTextSqlResult(search_query=search_box, entity_slot_retrieve=entity_slot_retrieve,
                                                retrieve_result=retrieve_result, response=response, sql="")
            search_result.entity_slot_retrieve = entity_slot_retrieve
            search_result.retrieve_result = retrieve_result
            search_result.response = response
            search_result.sql = sql
    except Exception as e:
        logger.error(e)
    return search_result


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

    if 'selected_sample' not in st.session_state:
        st.session_state['selected_sample'] = ''

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

    if 'nlq_chain' not in st.session_state:
        st.session_state['nlq_chain'] = None

    if "messages" not in st.session_state:
        st.session_state.messages = {}

    if "current_sql_result" not in st.session_state:
        st.session_state.current_sql_result = {}

    model_ids = ['anthropic.claude-3-sonnet-20240229-v1:0', 'anthropic.claude-3-5-sonnet-20240620-v1:0', 'anthropic.claude-3-opus-20240229-v1:0',
                 'anthropic.claude-3-haiku-20240307-v1:0', 'mistral.mixtral-8x7b-instruct-v0:1',
                 'meta.llama3-70b-instruct-v1:0']

    session_state_list = list(st.session_state.get('profiles', {}).keys())

    hava_session_state_flag = False
    if len(session_state_list) > 0:
        hava_session_state_flag = True

    with st.sidebar:
        st.title('Setting')
        # The default option can be the first one in the profiles dictionary, if exists

        selected_profile = st.selectbox("Data Profile", list(st.session_state.get('profiles', {}).keys()))
        if selected_profile != st.session_state.current_profile:
            # clear session state
            st.session_state.selected_sample = ''
            st.session_state.current_profile = selected_profile
            if selected_profile not in st.session_state.messages:
                st.session_state.messages[selected_profile] = []
            st.session_state.nlq_chain = NLQChain(selected_profile)

        model_type = st.selectbox("Choose your model", model_ids)

        use_rag_flag = st.checkbox("Using RAG from Q/A Embedding", True)
        visualize_results_flag = st.checkbox("Visualize Results", True)
        intent_ner_recognition_flag = st.checkbox("Intent NER", True)
        agent_cot_flag = st.checkbox("Agent COT", True)
        explain_gen_process_flag = st.checkbox("Explain Generation Process", True)
        data_with_analyse = st.checkbox("Answer With Insights", False)
        gen_suggested_question_flag = st.checkbox("Generate Suggested Questions", False)
        context_window = st.slider("Multiple Rounds of Context Window", 0, 10, 0)

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

    reject_intent_flag = False
    search_intent_flag = False
    agent_intent_flag = False
    knowledge_search_flag = False

    # add select box for which model to use
    if search_box != "Type your query here..." or \
            current_nlq_chain.is_visualization_config_changed():
        if search_box is not None and len(search_box) > 0:
            with st.chat_message("user"):
                current_nlq_chain.set_question(search_box)
                st.session_state.messages[selected_profile].append(
                    {"role": "user", "content": search_box, "type": "text"})
                st.markdown(current_nlq_chain.get_question())
            with st.chat_message("assistant"):
                filter_deep_dive_sql_result = []
                entity_slot = []
                normal_search_result = None
                agent_search_result = []
                agent_cot_task_result = {}

                database_profile = st.session_state.profiles[selected_profile]

                with st.spinner('Connecting to database...'):
                    # fix db url is Empty
                    if database_profile['db_url'] == '':
                        conn_name = database_profile['conn_name']
                        db_url = ConnectionManagement.get_db_url_by_name(conn_name)
                        database_profile['db_url'] = db_url
                        database_profile['db_type'] = ConnectionManagement.get_db_type_by_name(conn_name)
                    prompt_map = database_profile['prompt_map']
                    for key in prompt_map_dict:
                        if key not in prompt_map:
                            prompt_map[key] = prompt_map_dict[key]
                    ProfileManagement.update_table_prompt_map(selected_profile, prompt_map)

                # Multiple rounds of dialogue, query rewriting
                user_query_history = get_user_history(selected_profile)
                if len(user_query_history) > 0 and context_window > 0:
                    with st.status("Query Context Understanding") as status_text:
                        user_query_history = user_query_history[-context_window:]
                        logger.info("The Chat history is {history}".format(history=",".join(user_query_history)))
                        new_search_box = get_query_rewrite(model_type, search_box, prompt_map, user_query_history)
                        logger.info("The Origin query is {query}  query rewrite is {new_query}".format(query=search_box,
                                                                                                       new_query=new_search_box))
                        search_box = new_search_box
                        st.write(search_box)
                    status_text.update(label=f"Query Context Rewrite Completed", state="complete", expanded=False)
                intent_response = {
                    "intent": "normal_search",
                    "slot": []
                }
                # 通过标志位控制后续的逻辑
                # 主要的意图有4个, 拒绝, 查询, 思维链, 知识问答
                if intent_ner_recognition_flag:
                    with st.status("Performing intent recognition...") as status_text:
                        intent_response = get_query_intent(model_type, search_box, prompt_map)
                        intent = intent_response.get("intent", "normal_search")
                        entity_slot = intent_response.get("slot", [])
                        st.write(intent_response)
                        status_text.update(label=f"Intent Recognition Completed: This is a **{intent}** question",
                                           state="complete", expanded=False)
                        if intent == "reject_search":
                            reject_intent_flag = True
                            search_intent_flag = False
                        elif intent == "agent_search":
                            agent_intent_flag = True
                            if agent_cot_flag:
                                search_intent_flag = False
                            else:
                                search_intent_flag = True
                                agent_intent_flag = False
                        elif intent == "knowledge_search":
                            knowledge_search_flag = True
                            search_intent_flag = False
                            agent_intent_flag = False
                        else:
                            search_intent_flag = True
                else:
                    search_intent_flag = True

                # 主要的逻辑部分，调用LLM
                if reject_intent_flag:
                    st.write("Your query statement is currently not supported by the system")

                elif search_intent_flag:
                    # 执行普通的查询，并可视化结果
                    normal_search_result = normal_text_search_streamlit(search_box, model_type,
                                                                        database_profile,
                                                                        entity_slot, opensearch_info,
                                                                        selected_profile,
                                                                        explain_gen_process_flag, use_rag_flag)
                elif knowledge_search_flag:
                    with st.spinner('Performing knowledge search...'):
                        response = knowledge_search(search_box=search_box, model_id=model_type,
                                                    prompt_map=prompt_map)
                        logger.info(f'got llm response for knowledge_search: {response}')
                        st.markdown(f'This is a knowledge search question.\n{response}')

                elif agent_intent_flag:
                    with st.spinner('Analysis Of Complex Problems'):
                        agent_cot_retrieve = get_retrieve_opensearch(opensearch_info, search_box, "agent",
                                                                     selected_profile, 2, 0.5)
                        agent_cot_task_result = get_agent_cot_task(model_type, prompt_map, search_box,
                                                                   database_profile['tables_info'],
                                                                   agent_cot_retrieve)
                    with st.expander(f'Agent Query Retrieve : {len(agent_cot_retrieve)}'):
                        agent_examples = []
                        for example in agent_cot_retrieve:
                            agent_examples.append({'Score': example['_score'],
                                                   'Question': example['_source']['query'],
                                                   'Answer': example['_source']['comment'].strip()})
                        st.write(agent_examples)
                    with st.expander(f'Agent Task : {len(agent_cot_task_result)}'):
                        st.write(agent_cot_task_result)

                    with st.spinner('Generate SQL For Multiple Sub Problems'):
                        agent_search_result = agent_text_search(search_box, model_type,
                                                                database_profile,
                                                                entity_slot, opensearch_info,
                                                                selected_profile, use_rag_flag, agent_cot_task_result)
                else:
                    st.error("Intent recognition error")

                # 前端结果显示agent cot任务拆分信息, normal_text_search 的显示，做了拆分，为了方便跟API逻辑一致
                if search_intent_flag:
                    if normal_search_result.sql != "":
                        current_nlq_chain.set_generated_sql(normal_search_result.sql)
                        # st.code(normal_search_result.sql, language="sql")

                        current_nlq_chain.set_generated_sql_response(normal_search_result.response)

                        if explain_gen_process_flag:
                            with st.status("Generating explanations...") as status_text:
                                st.markdown(current_nlq_chain.get_generated_sql_explain())
                                status_text.update(
                                    label=f"Generating explanations Done",
                                    state="complete", expanded=False)
                        st.session_state.messages[selected_profile].append(
                            {"role": "assistant", "content": "SQL:" + normal_search_result.sql, "type": "sql"})
                    else:
                        st.write("Unable to generate SQL at the moment, please provide more information")
                elif agent_intent_flag:
                    with st.expander(f'Agent Task Result: {len(agent_search_result)}'):
                        st.write(agent_search_result)

                # 连接数据库，执行SQL, 记录历史记录并展示
                if search_intent_flag:
                    with st.spinner('Executing query...'):
                        search_intent_result = get_sql_result_tool(
                            st.session_state['profiles'][current_nlq_chain.profile],
                            current_nlq_chain.get_generated_sql())
                    if search_intent_result["status_code"] == 500:
                        with st.expander("The SQL Error Info"):
                            st.markdown(search_intent_result["error_info"])
                    else:
                        if search_intent_result["data"] is not None and len(
                                search_intent_result["data"]) > 0 and data_with_analyse:
                            with st.spinner('Generating data summarize...'):
                                search_intent_analyse_result = data_analyse_tool(model_type, prompt_map, search_box,
                                                                                 search_intent_result["data"].to_json(
                                                                                     orient='records',
                                                                                     force_ascii=False), "query")
                                st.markdown(search_intent_analyse_result)
                                st.session_state.messages[selected_profile].append(
                                    {"role": "assistant", "content": search_intent_analyse_result, "type": "text"})
                    st.session_state.current_sql_result[selected_profile] = search_intent_result["data"]

                elif agent_intent_flag:
                    for i in range(len(agent_search_result)):
                        each_task_res = get_sql_result_tool(
                            st.session_state['profiles'][current_nlq_chain.profile],
                            agent_search_result[i]["sql"])
                        if each_task_res["status_code"] == 200 and len(each_task_res["data"]) > 0:
                            agent_search_result[i]["data_result"] = each_task_res["data"].to_json(
                                orient='records')
                            filter_deep_dive_sql_result.append(agent_search_result[i])

                    agent_data_analyse_result = data_analyse_tool(model_type, prompt_map, search_box,
                                                                  json.dumps(filter_deep_dive_sql_result,
                                                                             ensure_ascii=False), "agent")
                    logger.info("agent_data_analyse_result")
                    logger.info(agent_data_analyse_result)
                    st.session_state.messages[selected_profile].append(
                        {"role": "user", "content": search_box, "type": "text"})
                    for i in range(len(filter_deep_dive_sql_result)):
                        st.write(filter_deep_dive_sql_result[i]["query"])
                        st.dataframe(pd.read_json(filter_deep_dive_sql_result[i]["data_result"],
                                                  orient='records'), hide_index=True)

                    st.session_state.messages[selected_profile].append(
                        {"role": "assistant", "content": filter_deep_dive_sql_result, "type": "pandas"})

                    st.markdown(agent_data_analyse_result)
                    current_nlq_chain.set_generated_sql_response(agent_data_analyse_result)
                    st.session_state.messages[selected_profile].append(
                        {"role": "assistant", "content": agent_data_analyse_result, "type": "text"})

                    st.markdown('You can provide feedback:')

                    # add a upvote(green)/downvote button with logo
                    feedback = st.columns(2)
                    feedback[0].button('👍 Upvote (save as embedding for retrieval)', type='secondary',
                                       use_container_width=True,
                                       on_click=upvote_agent_clicked,
                                       args=[current_nlq_chain.get_question(),
                                             agent_cot_task_result])

                    if feedback[1].button('👎 Downvote', type='secondary', use_container_width=True):
                        # do something here
                        pass

                # 数据可视化展示
                if visualize_results_flag and search_intent_flag:
                    current_search_sql_result = st.session_state.current_sql_result[selected_profile]
                    if current_search_sql_result is not None and len(current_search_sql_result) > 0:
                        st.session_state.messages[selected_profile].append(
                            {"role": "assistant", "content": current_search_sql_result, "type": "pandas"})
                        # Reset change flag to False
                        do_visualize_results(current_nlq_chain, st.session_state.current_sql_result[selected_profile])
                    else:
                        st.markdown("No relevant data found")

                # 生成推荐问题
                if gen_suggested_question_flag and (search_intent_flag or agent_intent_flag):
                    st.markdown('You might want to further ask:')
                    with st.spinner('Generating suggested questions...'):
                        generated_sq = generate_suggested_question(prompt_map, search_box, model_id=model_type)
                        split_strings = generated_sq.split("[generate]")
                        gen_sq_list = [s.strip() for s in split_strings if s.strip()]
                        sq_result = st.columns(3)
                        sq_result[0].button(gen_sq_list[0], type='secondary',
                                            use_container_width=True,
                                            on_click=sample_question_clicked,
                                            args=[gen_sq_list[0]])
                        sq_result[1].button(gen_sq_list[1], type='secondary',
                                            use_container_width=True,
                                            on_click=sample_question_clicked,
                                            args=[gen_sq_list[1]])
                        sq_result[2].button(gen_sq_list[2], type='secondary',
                                            use_container_width=True,
                                            on_click=sample_question_clicked,
                                            args=[gen_sq_list[2]])
        else:
            # st.error("Please enter a valid query.")
            if current_nlq_chain.is_visualization_config_changed():
                if visualize_results_flag:
                    do_visualize_results(current_nlq_chain, st.session_state.current_sql_result[selected_profile])


if __name__ == '__main__':
    main()
