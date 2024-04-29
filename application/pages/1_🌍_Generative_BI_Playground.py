import json
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import logging

from nlq.business.connection import ConnectionManagement
from nlq.business.nlq_chain import NLQChain
from nlq.business.profile import ProfileManagement
from nlq.business.suggested_question import SuggestedQuestionManagement as sqm
from nlq.business.vector_store import VectorStore
from utils.llm import text_to_sql, get_query_intent, generate_suggested_question, get_agent_cot_task, data_analyse_tool, \
    knowledge_search
from utils.constant import PROFILE_QUESTION_TABLE_NAME, ACTIVE_PROMPT_NAME, DEFAULT_PROMPT_NAME
from utils.navigation import make_sidebar
from utils.tool import get_generated_sql
from utils.opensearch import get_retrieve_opensearch
from utils.domain import SearchTextSqlResult
from utils.apis import get_sql_result_tool

logger = logging.getLogger(__name__)


def sample_question_clicked(sample):
    """Update the selected_sample variable with the text of the clicked button"""
    st.session_state['selected_sample'] = sample


def upvote_clicked(question, sql, env_vars):
    # HACK: configurable opensearch endpoint

    current_profile = st.session_state.current_profile
    VectorStore.add_sample(current_profile, question, sql)
    logger.info(f'up voted "{question}" with sql "{sql}"')


def upvote_agent_clicked(question, comment, env_vars):
    # HACK: configurable opensearch endpoint

    current_profile = st.session_state.current_profile
    VectorStore.add_agent_cot_sample(current_profile, question, str(comment))
    logger.info(f'up voted "{question}" with sql "{comment}"')


def clean_st_history(selected_profile):
    st.session_state.messages[selected_profile] = []


def do_visualize_results(nlq_chain, sql_result):
    # with st.chat_message("assistant"):
        # if nlq_chain.get_executed_result_df(st.session_state['profiles'][nlq_chain.profile],force_execute_query=False) is None:
        #     logger.info('try to execute the generated sql')
        #     with st.spinner('Querying database...'):
        #         sql_query_result = nlq_chain.get_executed_result_df(st.session_state['profiles'][nlq_chain.profile])
        # else:
        #     sql_query_result = nlq_chain.get_executed_result_df(st.session_state['profiles'][nlq_chain.profile])
    sql_query_result = sql_result
    st.markdown('Visualizing the results:')
    if sql_query_result is not None:
        # Reset change flag to False
        nlq_chain.set_visualization_config_change(False)
        # Auto-detect columns
        visualize_config_columns = st.columns(3)

        available_columns = sql_query_result.columns

        chart_type = visualize_config_columns[0].selectbox('Choose the chart type',
                                                               ['Table', 'Bar', 'Line', 'Pie'],
                                                               on_change=nlq_chain.set_visualization_config_change)
        if chart_type != 'Table':
            x_column = visualize_config_columns[1].selectbox('Choose x-axis column', available_columns,
                                                                 on_change=nlq_chain.set_visualization_config_change)
            y_column = visualize_config_columns[2].selectbox('Choose y-axis column',
                                                                 reversed(available_columns.to_list()),
                                                                 on_change=nlq_chain.set_visualization_config_change)
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


def normal_text_search(search_box, model_type, database_profile, entity_slot, env_vars, selected_profile, use_rag,
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

        if len(entity_slot) > 0 and use_rag:
            for each_entity in entity_slot:
                entity_retrieve = get_retrieve_opensearch(env_vars, each_entity, "ner",
                                                          selected_profile, 1, 0.7)
                if len(entity_retrieve) > 0:
                    entity_slot_retrieve.extend(entity_retrieve)

        if use_rag:
            retrieve_result = get_retrieve_opensearch(env_vars, search_box, "query",
                                                      selected_profile, 3, 0.5)

        response = text_to_sql(database_profile['tables_info'],
                               database_profile['hints'],
                               search_box,
                               model_id=model_type,
                               sql_examples=retrieve_result,
                               ner_example=entity_slot_retrieve,
                               dialect=database_profile['db_type'],
                               model_provider=model_provider)
        sql = get_generated_sql(response)
        search_result = SearchTextSqlResult(search_query=search_box, entity_slot_retrieve=entity_slot_retrieve,
                                            retrieve_result=retrieve_result, response=response, sql="")
        search_result.entity_slot_retrieve = entity_slot_retrieve
        search_result.retrieve_result = retrieve_result
        search_result.response = response
        search_result.sql = sql
    except Exception as e:
        logger.error(e)
    return search_result


def agent_text_search(search_box, model_type, database_profile, entity_slot, env_vars, selected_profile, use_rag,
                      agent_cot_task_result):
    agent_search_results = []
    try:
        for each_task in agent_cot_task_result:
            each_res_dict = {}
            each_task_query = agent_cot_task_result[each_task]
            each_res_dict["query"] = each_task_query
            entity_slot_retrieve = []
            retrieve_result = []
            if use_rag:
                entity_slot_retrieve = get_retrieve_opensearch(env_vars, each_task_query, "ner",
                                                               selected_profile, 3, 0.5)

                retrieve_result = get_retrieve_opensearch(env_vars, each_task_query, "query",
                                                          selected_profile, 3, 0.5)
            each_task_response = text_to_sql(database_profile['tables_info'],
                                             database_profile['hints'],
                                             each_task_query,
                                             model_id=model_type,
                                             sql_examples=retrieve_result,
                                             ner_example=entity_slot_retrieve,
                                             dialect=database_profile['db_type'],
                                             model_provider=None)
            each_task_sql = get_generated_sql(each_task_response)
            each_res_dict["response"] = each_task_response
            each_res_dict["sql"] = each_task_sql
            if each_res_dict["sql"] != "":
                agent_search_results.append(each_res_dict)
    except Exception as e:
        logger.error(e)
    return agent_search_results


def main():
    load_dotenv()

    # load config.json as dictionary
    with open(os.path.join(os.getcwd(), 'config_files', '1_config.json')) as f:
        env_vars = json.load(f)
        opensearch_config = env_vars['data_sources']['shopping_guide']['opensearch']
        for key in opensearch_config:
            opensearch_config[key] = os.getenv(opensearch_config[key].replace('$', ''))
        # logger.info(f'{opensearch_config=}')

    st.set_page_config(page_title="Demo", layout="wide")
    make_sidebar()

    # Title and Description
    st.title('Generative BI Playground')
    st.write("""
    Welcome to the Generative BI Playground! This interactive application is designed to bridge the gap between natural language and databases. 
    Enter your query in plain English, and watch as it's transformed into a SQL. The result can then be visualized, giving you insights without needing to write any code. 
    Experiment, learn, and see the power of Generative BI in action!
    """)
    st.divider()

    demo_profile_suffix = '(demo)'
    # Initialize or set up state variables
    if 'profiles' not in st.session_state:
        demo_profile = {}
        for i, v in env_vars['data_sources'].items():
            if 'is_demo' in v and v['is_demo']:
                demo_profile[i + demo_profile_suffix] = v

        # get all user defined profiles with info (db_url, conn_name, tables_info, hints, search_samples)
        all_profiles = ProfileManagement.get_all_profiles_with_info()
        all_profiles.update(demo_profile)
        st.session_state['profiles'] = all_profiles
        # logger.info(f'{all_profiles=}')

    # if 'option' not in st.session_state:
    #     st.session_state['option'] = 'Text2SQL'

    if 'selected_sample' not in st.session_state:
        st.session_state['selected_sample'] = ''

    if 'dataframe' not in st.session_state:
        st.session_state['dataframe'] = pd.DataFrame({
            'column1': ['A', 'B', 'C'],
            'column2': [1, 2, 3]
        })

    if 'current_profile' not in st.session_state:
        st.session_state['current_profile'] = ''

    if 'nlq_chain' not in st.session_state:
        st.session_state['nlq_chain'] = None

    if "messages" not in st.session_state:
        st.session_state.messages = {}

    if "current_sql_result" not in st.session_state:
        st.session_state.current_sql_result = {}

    model_ids = ['anthropic.claude-3-sonnet-20240229-v1:0', 'anthropic.claude-3-opus-20240229-v1:0',
                 'anthropic.claude-3-haiku-20240307-v1:0', 'mistral.mixtral-8x7b-instruct-v0:1',
                 'meta.llama3-70b-instruct-v1:0']

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

        # st.session_state['option'] = st.selectbox("Choose your option", ["Text2SQL"])
        model_type = st.selectbox("Choose your model", model_ids)
        model_provider = None

        use_rag = st.checkbox("Using RAG from Q/A Embedding", True)
        visualize_results = st.checkbox("Visualize Results", True)
        intent_ner_recognition = st.checkbox("Intent NER", True)
        agent_cot = st.checkbox("Agent COT", False)
        explain_gen_process_flag = st.checkbox("Explain Generation Process", True)
        gen_suggested_question = st.checkbox("Generate Suggested Questions", False)

        clean_history = st.button("clean history", on_click=clean_st_history, args=[selected_profile])

    # Part II: Search Section
    st.subheader("Start Searching")

    st.caption('Profile description:')
    comments = st.session_state.profiles[selected_profile]['comments']
    comments_text = comments.split("Examples:")[0]
    comments_questions = []
    if len(comments.split("Examples:")) > 1:
        comments_questions_txt = comments.split("Examples:")[1]
        comments_questions = [i for i in comments_questions_txt.split("\n") if i != '']

    st.write(comments_text)

    st.info("Quick Start: Click on the following buttons to start searching.")

    # Pre-written search samples
    search_samples = st.session_state.profiles[selected_profile]['search_samples']
    search_samples = search_samples + comments_questions

    question_column_number = 3
    # Create columns for the predefined search samples
    search_sample_columns = st.columns(question_column_number)

    # Display the predefined search samples as buttons within columns
    for i, sample in enumerate(search_samples[0:question_column_number]):
        search_sample_columns[i].button(sample, use_container_width=True, on_click=sample_question_clicked,
                                        args=[sample])

    # Display more predefined search samples as buttons within columns, if there are more samples than columns
    if len(search_samples) > question_column_number:
        with st.expander('More questions...'):
            more_sample_columns = st.columns(question_column_number)
            col_num = 0
            for i, sample in enumerate(search_samples[question_column_number:]):
                more_sample_columns[col_num].button(sample, use_container_width=True, on_click=sample_question_clicked,
                                                    args=[sample])
                if col_num == question_column_number - 1:
                    col_num = 0
                else:
                    col_num += 1

    # Display chat messages from history
    if selected_profile in st.session_state.messages:
        for message in st.session_state.messages[selected_profile]:
            with st.chat_message(message["role"]):
                if "SQL:" in message["content"]:
                    with st.expander("The generated SQL"):
                        st.code(message["content"].replace("SQL:", ""), language="sql")
                elif isinstance(message["content"], pd.DataFrame):
                    st.dataframe(message["content"], hide_index=True)
                elif isinstance(message["content"], list):
                    for each_content in message["content"]:
                        st.write(each_content["query"])
                        st.dataframe(pd.read_json(each_content["data_result"], orient='records'), hide_index=True)
                else:
                    st.markdown(message["content"])

    text_placeholder = "Type your query here..."

    search_box = st.chat_input(placeholder=text_placeholder)
    if st.session_state['selected_sample'] != "":
        search_box = st.session_state['selected_sample']
        st.session_state['selected_sample'] = ""

    current_nlq_chain = st.session_state.nlq_chain

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
                st.markdown(current_nlq_chain.get_question())
            with st.chat_message("assistant"):
                # retrieve_result = []
                # entity_slot_retrieve = []
                # deep_dive_sql_result = []
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

                # 通过标志位控制后续的逻辑
                # 主要的意图有4个, 拒绝, 查询, 思维链, 知识问答
                if intent_ner_recognition:
                    with st.spinner('Performing intent recognition...'):
                        intent_response = get_query_intent(model_type, search_box)
                        intent = intent_response.get("intent", "normal_search")
                        entity_slot = intent_response.get("slot", [])
                        st.markdown(f'This is a {intent} question.')
                        if intent == "reject_search":
                            reject_intent_flag = True
                            search_intent_flag = False
                        elif intent == "agent_search":
                            agent_intent_flag = True
                            if agent_cot:
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
                    with st.spinner('Generating SQL... (Take up to 20s)'):
                        normal_search_result = normal_text_search(search_box, model_type,
                                                                  database_profile,
                                                                  entity_slot, env_vars,
                                                                  selected_profile, use_rag)
                elif knowledge_search_flag:
                    with st.spinner('Performing knowledge search...'):
                        response = knowledge_search(search_box=search_box, model_id=model_type)
                        logger.info(f'got llm response for knowledge_search: {response}')
                        st.markdown(f'This is a knowledge search question.\n{response}')

                else:
                    st.markdown("This is a complex business problem, and the problem is being broken down.")
                    with st.spinner('Generating SQL... (Take up to 40s)'):
                        agent_cot_retrieve = get_retrieve_opensearch(env_vars, search_box, "agent",
                                                                     selected_profile, 2, 0.5)
                        agent_cot_task_result = get_agent_cot_task(model_type, search_box,
                                                                   database_profile['tables_info'],
                                                                   agent_cot_retrieve)
                        with st.expander(f'Agent Query Retrieve : {len(agent_cot_retrieve)}'):
                            st.write(agent_cot_retrieve)
                        with st.expander(f'Agent Task : {len(agent_cot_task_result)}'):
                            st.write(agent_cot_task_result)
                        agent_search_result = agent_text_search(search_box, model_type,
                                                                database_profile,
                                                                entity_slot, env_vars,
                                                                selected_profile, use_rag, agent_cot_task_result)

                # 前端结果显示部分，显示召回的数据或者agent cot任务拆分信息
                if search_intent_flag:
                    with st.expander(
                            f'Query Retrieve : {len(normal_search_result.retrieve_result)}, NER Retrieve : {len(normal_search_result.entity_slot_retrieve)}'):
                        examples = {}
                        examples["query_retrieve"] = []
                        for example in normal_search_result.retrieve_result:
                            examples["query_retrieve"].append({'Score': example['_score'],
                                                               'Question': example['_source']['text'],
                                                               'Answer': example['_source']['sql'].strip()})
                        examples["ner_retrieve"] = []
                        for example in normal_search_result.entity_slot_retrieve:
                            examples["ner_retrieve"].append({'Score': example['_score'],
                                                             'Question': example['_source']['entity'],
                                                             'Answer': example['_source']['comment'].strip()})
                        st.write(examples)
                elif agent_intent_flag:
                    with st.expander(f'Agent Task Result: {len(agent_search_result)}'):
                        st.write(agent_search_result)

                # 连接数据库，执行SQL, 记录历史记录并展示
                if search_intent_flag:
                    st.session_state.messages[selected_profile].append({"role": "user", "content": search_box})
                    if normal_search_result.sql != "":
                        current_nlq_chain.set_generated_sql(normal_search_result.sql)
                        with st.expander("The generated SQL"):
                            st.code(normal_search_result.sql, language="sql")
                            
                            current_nlq_chain.set_generated_sql_response(normal_search_result.response)
                            
                            if explain_gen_process_flag:
                                with st.spinner('Generating explanations...'):
                                    st.session_state.messages[selected_profile].append(
                                        {"role": "assistant", "content": current_nlq_chain.get_generated_sql_explain()})
                                    st.markdown(current_nlq_chain.get_generated_sql_explain())
                                    print(current_nlq_chain.get_generated_sql_explain())

                            # add a upvote(green)/downvote button with logo
                            feedback = st.columns(2)
                            feedback[0].button('👍 Upvote (save as embedding for retrieval)', type='secondary',
                                                use_container_width=True,
                                                on_click=upvote_clicked,
                                                args=[current_nlq_chain.get_question(),
                                                        current_nlq_chain.get_generated_sql(),
                                                        env_vars])

                            if feedback[1].button('👎 Downvote', type='secondary', use_container_width=True):
                                # do something here
                                pass

                        st.session_state.messages[selected_profile].append(
                            {"role": "assistant", "content": "SQL:" + normal_search_result.sql})
                    else:
                        st.write("Unable to generate SQL at the moment, please provide more information")

                    search_intent_result = get_sql_result_tool(st.session_state['profiles'][current_nlq_chain.profile],
                                                                current_nlq_chain.get_generated_sql())
                    if search_intent_result["status_code"] == 500:
                        with st.expander("The SQL Error Info"):
                            st.markdown(search_intent_result["error_info"])
                    else:
                        if search_intent_result["data"] is not None and len(search_intent_result["data"]) > 0:
                            search_intent_analyse_result = data_analyse_tool(model_type, search_box,
                                                                           search_intent_result["data"].to_json(orient='records', force_ascii=False), "query")
                            st.markdown(search_intent_analyse_result)
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

                    agent_data_analyse_result = data_analyse_tool(model_type, search_box,
                                                                       json.dumps(filter_deep_dive_sql_result, ensure_ascii=False), "agent")
                    logger.info("agent_data_analyse_result")
                    logger.info(agent_data_analyse_result)
                    st.session_state.messages[selected_profile].append(
                        {"role": "user", "content": search_box})
                    for i in range(len(filter_deep_dive_sql_result)):
                        st.write(filter_deep_dive_sql_result[i]["query"])
                        st.dataframe(pd.read_json(filter_deep_dive_sql_result[i]["data_result"],
                                                  orient='records'), hide_index=True)

                    st.session_state.messages[selected_profile].append(
                        {"role": "assistant", "content": filter_deep_dive_sql_result})

                    st.markdown(agent_data_analyse_result)
                    current_nlq_chain.set_generated_sql_response(agent_data_analyse_result)
                    st.session_state.messages[selected_profile].append(
                        {"role": "assistant", "content": agent_data_analyse_result})

                    st.markdown('You can provide feedback:')

                    # add a upvote(green)/downvote button with logo
                    feedback = st.columns(2)
                    feedback[0].button('👍 Upvote (save as embedding for retrieval)', type='secondary',
                                       use_container_width=True,
                                       on_click=upvote_agent_clicked,
                                       args=[current_nlq_chain.get_question(),
                                             agent_cot_task_result,
                                             env_vars])

                    if feedback[1].button('👎 Downvote', type='secondary', use_container_width=True):
                        # do something here
                        pass

                # 数据可视化展示
                if visualize_results and search_intent_flag:
                    current_search_sql_result = st.session_state.current_sql_result[selected_profile]
                    if current_search_sql_result is not None and len(current_search_sql_result) > 0:
                        st.session_state.messages[selected_profile].append(
                            {"role": "assistant", "content": current_search_sql_result})
                        do_visualize_results(current_nlq_chain, st.session_state.current_sql_result[selected_profile])
                    else:
                        st.markdown("No relevant data found")

                # 生成推荐问题
                if gen_suggested_question and (search_intent_flag or agent_intent_flag):
                    st.markdown('You might want to further ask:')
                    active_prompt = sqm.get_prompt_by_name(ACTIVE_PROMPT_NAME).prompt
                    with st.spinner('Generating suggested questions...'):
                        generated_sq = generate_suggested_question(search_box, active_prompt, model_id=model_type)
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
                if visualize_results:
                    do_visualize_results(current_nlq_chain, st.session_state.current_sql_result[selected_profile])


if __name__ == '__main__':
    main()
