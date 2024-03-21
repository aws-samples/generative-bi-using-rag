import json
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from loguru import logger

from nlq.business.connection import ConnectionManagement
from nlq.business.nlq_chain import NLQChain
from nlq.business.profile import ProfileManagement
from utils.database import get_db_url_dialect
from nlq.business.vector_store import VectorStore
from utils.llm import claude3_to_sql, create_vector_embedding_with_bedrock, retrieve_results_from_opensearch, \
    upload_results_to_opensearch, get_query_intent


def sample_question_clicked(sample):
    """Update the selected_sample variable with the text of the clicked button"""
    st.session_state['selected_sample'] = sample


def upvote_clicked(question, sql, env_vars):
    # HACK: configurable opensearch endpoint

    current_profile = st.session_state.current_profile
    VectorStore.add_sample(current_profile, question, sql)
    logger.info(f'up voted "{question}" with sql "{sql}"')


def do_visualize_results(nlq_chain):
    with st.chat_message("assistant"):
        if nlq_chain.get_executed_result_df(force_execute_query=False) is None:
            logger.info('try to execute the generated sql')
            with st.spinner('Querying database...'):
                sql_query_result = nlq_chain.get_executed_result_df()
        else:
            sql_query_result = nlq_chain.get_executed_result_df()
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
                st.table(sql_query_result)
            elif chart_type == 'Bar':
                st.plotly_chart(px.bar(sql_query_result, x=x_column, y=y_column))
            elif chart_type == 'Line':
                st.plotly_chart(px.line(sql_query_result, x=x_column, y=y_column))
            elif chart_type == 'Pie':
                st.plotly_chart(px.pie(sql_query_result, names=x_column, values=y_column))
        else:
            st.markdown('No visualization generated.')


def main():
    load_dotenv()

    # load config.json as dictionary
    with open(os.path.join(os.getcwd(), 'config_files', '1_config.json')) as f:
        env_vars = json.load(f)
        opensearch_config = env_vars['data_sources']['shopping_guide']['opensearch']
        for key in opensearch_config:
            opensearch_config[key] = os.getenv(opensearch_config[key].replace('$', ''))
        # logger.info(f'{opensearch_config=}')

    st.set_page_config(layout="wide")

    # Title and Description
    st.title('Natural Language Querying Playground')
    st.write("""
    Welcome to the Natural Language Querying Playground! This interactive application is designed to bridge the gap between natural language and databases. 
    Enter your query in plain English, and watch as it's transformed into a SQL or Pandas command. The result can then be visualized, giving you insights without needing to write any code. 
    Experiment, learn, and see the power of NLQ in action!
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

    if 'option' not in st.session_state:
        st.session_state['option'] = 'Text2SQL'

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

    bedrock_model_ids = ['anthropic.claude-3-sonnet-20240229-v1:0', 'anthropic.claude-3-haiku-20240307-v1:0',
                         'anthropic.claude-v2:1']

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

        st.session_state['option'] = st.selectbox("Choose your option", ["Text2SQL"])
        model_type = st.selectbox("Choose your model", bedrock_model_ids)
        model_provider = None

        use_rag = st.checkbox("Using RAG from Q/A Embedding", True)
        visualize_results = st.checkbox("Visualize Results", True)

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
    # logger.info(f'{st.session_state.profiles=}')
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
                    st.code(message["content"].replace("SQL:", ""), language="sql")
                elif isinstance(message["content"], pd.DataFrame):
                    st.table(message["content"])
                else:
                    st.markdown(message["content"])

    text_placeholder = "Type your query here..."

    search_box = st.chat_input(placeholder=text_placeholder)
    if st.session_state['selected_sample'] != "":
        search_box = st.session_state['selected_sample']
        st.session_state['selected_sample'] = ""

    current_nlq_chain = st.session_state.nlq_chain

    search_intent_flag = True

    # add select box for which model to use
    if search_box != "Type your query here..." or \
            current_nlq_chain.is_visualization_config_changed():
        if search_box is not None and len(search_box) > 0:
            with st.chat_message("user"):
                current_nlq_chain.set_question(search_box)
                st.markdown(current_nlq_chain.get_question())
            with st.chat_message("assistant"):
                retrieve_result = []
                if not current_nlq_chain.get_retrieve_samples():
                    logger.info(f'try to get retrieve samples from open search')
                    with st.spinner('Retrieving Q/A (Take up to 5s)'):
                        logger.info('Retrieving samples...')
                        retrieve_result = None
                        if use_rag:
                            try:
                                # HACK: always use first opensearch
                                origin_selected_profile = selected_profile
                                selected_profile = "shopping_guide"

                                records_with_embedding = create_vector_embedding_with_bedrock(
                                    search_box,
                                    index_name=env_vars['data_sources'][selected_profile]['opensearch']['index_name'])
                                retrieve_result = retrieve_results_from_opensearch(
                                    index_name=env_vars['data_sources'][selected_profile]['opensearch']['index_name'],
                                    region_name=env_vars['data_sources'][selected_profile]['opensearch']['region_name'],
                                    domain=env_vars['data_sources'][selected_profile]['opensearch']['domain'],
                                    opensearch_user=env_vars['data_sources'][selected_profile]['opensearch'][
                                        'opensearch_user'],
                                    opensearch_password=env_vars['data_sources'][selected_profile]['opensearch'][
                                        'opensearch_password'],
                                    host=env_vars['data_sources'][selected_profile]['opensearch'][
                                        'opensearch_host'],
                                    port=env_vars['data_sources'][selected_profile]['opensearch'][
                                        'opensearch_port'],
                                    query_embedding=records_with_embedding['vector_field'],
                                    top_k=3,
                                    profile_name=origin_selected_profile.replace(demo_profile_suffix, ''))
                                selected_profile = origin_selected_profile

                                current_nlq_chain.set_retrieve_samples(retrieve_result)
                            except Exception as e:
                                logger.exception(e)
                                logger.info(f"Failed to retrieve Q/A from OpenSearch: {str(e)}")
                                retrieve_result = []
                                selected_profile = origin_selected_profile
                else:
                    logger.info(f'get retrieve samples from memory: {len(current_nlq_chain.get_retrieve_samples())}')

                with st.expander(f'Retrieve result: {len(current_nlq_chain.get_retrieve_samples())}'):
                    examples = []
                    for example in current_nlq_chain.get_retrieve_samples():
                        examples.append({'Score': example['_score'],
                                         'Question': example['_source']['text'],
                                         'Answer': example['_source']['sql'].strip()})
                    st.write(examples)

                if not current_nlq_chain.get_generated_sql_response():
                    logger.info('try to get generated sql from LLM')
                    with st.spinner('Generating SQL... (Take up to 20s)'):
                        # Whether Retrieving Few Shots from Database
                        logger.info('Sending request...')
                        database_profile = st.session_state.profiles[selected_profile]
                        # fix db url is Empty
                        if database_profile['db_url'] == '':
                            conn_name = database_profile['conn_name']
                            db_url = ConnectionManagement.get_db_url_by_name(conn_name)
                            database_profile['db_url'] = db_url

                        intent_response = get_query_intent(model_type, search_box)

                        intent = intent_response.get("intent", "normal_search")
                        if intent == "reject_search":
                            search_intent_flag = False

                        if search_intent_flag:
                            response = claude3_to_sql(database_profile['tables_info'],
                                                      database_profile['hints'],
                                                      search_box,
                                                      model_id=model_type,
                                                      examples=retrieve_result,
                                                      dialect=get_db_url_dialect(database_profile['db_url']),
                                                      model_provider=model_provider)

                            logger.info(f'got llm response: {response}')
                            current_nlq_chain.set_generated_sql_response(response)
                else:
                    logger.info('get generated sql from memory')

                if search_intent_flag:
                    # Add user message to chat history
                    st.session_state.messages[selected_profile].append({"role": "user", "content": search_box})

                    # Add assistant response to chat history
                    st.session_state.messages[selected_profile].append(
                        {"role": "assistant", "content": "SQL:" + current_nlq_chain.get_generated_sql()})
                    st.session_state.messages[selected_profile].append(
                        {"role": "assistant", "content": current_nlq_chain.get_generated_sql_explain()})

                    st.markdown('The generated SQL statement is:')
                    st.code(current_nlq_chain.get_generated_sql(), language="sql")

                    st.markdown('Generation process explanations:')
                    st.markdown(current_nlq_chain.get_generated_sql_explain())

                    st.markdown('You can provide feedback:')

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
                else:
                    st.markdown('Your query statement is currently not supported by the system')

            if visualize_results and search_intent_flag:
                do_visualize_results(current_nlq_chain)
        else:
            st.error("Please enter a valid query.")


if __name__ == '__main__':
    main()
