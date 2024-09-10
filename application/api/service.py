import json
from typing import Union
from dotenv import load_dotenv

from nlq.business.connection import ConnectionManagement
from nlq.business.datasource.factory import DataSourceFactory
from nlq.business.log_feedback import FeedBackManagement
from nlq.business.model import ModelManagement
from nlq.business.nlq_chain import NLQChain
from nlq.business.profile import ProfileManagement
from nlq.business.vector_store import VectorStore
from nlq.business.log_store import LogManagement
from nlq.core.chat_context import ProcessingContext
from nlq.core.state import QueryState
from nlq.core.state_machine import QueryStateMachine
from utils.database import get_db_url_dialect
from utils.domain import SearchTextSqlResult
from utils.llm import text_to_sql, get_query_intent
from utils.logging import getLogger
from utils.opensearch import get_retrieve_opensearch
from utils.env_var import opensearch_info
from utils.tool import generate_log_id, get_current_time, get_generated_sql, serialize_timestamp
from .schemas import Question, Example, Option,  Message, HistoryMessage
from .exception_handler import BizException
from utils.constant import BEDROCK_MODEL_IDS
from .enum import ErrorEnum, ContentEnum
from fastapi import WebSocket

logger = getLogger()

load_dotenv()


def get_option() -> Option:
    all_profiles = ProfileManagement.get_all_profiles_with_info()
    all_sagemaker = ModelManagement.get_all_models()
    all_model_list = BEDROCK_MODEL_IDS
    for model_name in all_sagemaker:
        if model_name not in all_model_list:
            all_model_list.append(model_name)
    option = Option(
        data_profiles=all_profiles.keys(),
        bedrock_model_ids=all_model_list,
    )
    return option


def verify_parameters(question: Question):
    if question.bedrock_model_id not in BEDROCK_MODEL_IDS:
        raise BizException(ErrorEnum.INVAILD_BEDROCK_MODEL_ID)


def get_example(current_nlq_chain: NLQChain) -> list[Example]:
    examples = []
    for example in current_nlq_chain.get_retrieve_samples():
        examples.append(Example(
            score=example['_score'],
            question=example['_source']['text'],
            answer=example['_source']['sql'].strip()
        )
        )
    return examples


def get_history_by_user_profile(user_id: str, profile_name: str):
    history_list = LogManagement.get_history(user_id, profile_name)
    chat_history = []
    chat_history_session = {}
    for item in history_list:
        session_id = item['session_id']
        if session_id not in chat_history_session:
            chat_history_session[session_id] = []
        log_info = item['log_info']
        query = item['query']
        human_message = Message(type="human", content=query)
        bot_message = Message(type="AI", content=json.loads(log_info))
        chat_history_session[session_id].append(human_message)
        chat_history_session[session_id].append(bot_message)

    for key, value in chat_history_session.items():
        each_session_history = HistoryMessage(session_id=key, messages=value)
        chat_history.append(each_session_history)
    return chat_history


def get_result_from_llm(question: Question, current_nlq_chain: NLQChain, with_response_stream=False) -> Union[
    str, dict]:
    logger.info('try to get generated sql from LLM')

    entity_slot_retrieve = []
    all_profiles = ProfileManagement.get_all_profiles_with_info()
    database_profile = all_profiles[question.profile_name]
    if question.intent_ner_recognition:
        intent_response = get_query_intent(question.bedrock_model_id, question.keywords, database_profile['prompt_map'])
        intent = intent_response.get("intent", "normal_search")
        if intent == "reject_search":
            raise BizException(ErrorEnum.NOT_SUPPORTED)
        entity_slot = intent_response.get("slot", [])
        if entity_slot:
            for each_entity in entity_slot:
                entity_retrieve = get_retrieve_opensearch(opensearch_info, each_entity, "ner", question.profile_name, 1,
                                                          0.7)
                if entity_retrieve:
                    entity_slot_retrieve.extend(entity_retrieve)

    # Whether Retrieving Few Shots from Database
    logger.info('Sending request...')
    # fix db url is Empty
    if database_profile['db_url'] == '':
        conn_name = database_profile['conn_name']
        db_url = ConnectionManagement.get_db_url_by_name(conn_name)
        database_profile['db_url'] = db_url

    response = text_to_sql(database_profile['tables_info'],
                            database_profile['hints'],
                            database_profile['prompt_map'],
                            question.keywords,
                            model_id=question.bedrock_model_id,
                            sql_examples=current_nlq_chain.get_retrieve_samples(),
                            ner_example=entity_slot_retrieve,
                            dialect=get_db_url_dialect(database_profile['db_url']),
                            model_provider=None,
                            with_response_stream=with_response_stream, )
    return response


async def ask_websocket(websocket: WebSocket, question: Question):
    logger.info(question)
    session_id = question.session_id
    user_id = question.user_id
    username = question.username

    intent_ner_recognition_flag = question.intent_ner_recognition_flag
    agent_cot_flag = question.agent_cot_flag

    model_type = question.bedrock_model_id
    search_box = question.query
    selected_profile = question.profile_name
    use_rag_flag = question.use_rag_flag
    explain_gen_process_flag = question.explain_gen_process_flag
    gen_suggested_question_flag = question.gen_suggested_question_flag
    answer_with_insights = question.answer_with_insights
    context_window = question.context_window

    log_id = generate_log_id()

    all_profiles = ProfileManagement.get_all_profiles_with_info()
    database_profile = all_profiles[selected_profile]

    if database_profile['db_url'] == '':
        conn_name = database_profile['conn_name']
        db_url = ConnectionManagement.get_db_url_by_name(conn_name)
        database_profile['db_url'] = db_url
        database_profile['db_type'] = ConnectionManagement.get_db_type_by_name(conn_name)

    user_query_history = []
    if context_window > 0:
        user_query_history = LogManagement.get_history_by_session(profile_name=selected_profile, user_id=user_id,
                                                                  session_id=session_id, size=context_window,
                                                                  log_type='chat_history')
        user_query_history.append("user:" + search_box)

    if question.previous_intent == "entity_select":
        previous_state = QueryState.USER_SELECT_ENTITY.name
    else:
        previous_state = QueryState.INITIAL.name
    processing_context = ProcessingContext(
        search_box=search_box,
        query_rewrite=question.query_rewrite,
        session_id=session_id,
        user_id=user_id,
        username=username,
        selected_profile=selected_profile,
        database_profile=database_profile,
        model_type=model_type,
        use_rag_flag=use_rag_flag,
        intent_ner_recognition_flag=intent_ner_recognition_flag,
        agent_cot_flag=agent_cot_flag,
        explain_gen_process_flag=explain_gen_process_flag,
        visualize_results_flag=True,
        data_with_analyse=answer_with_insights,
        gen_suggested_question_flag=gen_suggested_question_flag,
        auto_correction_flag=True,
        context_window=context_window,
        entity_same_name_select={},
        user_query_history=user_query_history,
        opensearch_info=opensearch_info,
        previous_state=previous_state)

    state_machine = QueryStateMachine(processing_context)
    if state_machine.previous_state == QueryState.USER_SELECT_ENTITY:
        state_machine.transition(QueryState.USER_SELECT_ENTITY)
    while state_machine.get_state() != QueryState.COMPLETE and state_machine.get_state() != QueryState.ERROR:
        if state_machine.get_state() == QueryState.INITIAL:
            await response_websocket(websocket, session_id, "Query Rewrite", ContentEnum.STATE, "start",
                                     user_id)
            state_machine.handle_initial()
            await response_websocket(websocket, session_id, "Query Rewrite", ContentEnum.STATE, "end",
                                     user_id)
        elif state_machine.get_state() == QueryState.REJECT_INTENT:
            await response_websocket(websocket, session_id, "Reject Intent", ContentEnum.STATE, "start",
                                     user_id)
            state_machine.handle_reject_intent()
            await response_websocket(websocket, session_id, "Reject Intent", ContentEnum.STATE, "end",
                                     user_id)
        elif state_machine.get_state() == QueryState.KNOWLEDGE_SEARCH:
            await response_websocket(websocket, session_id, "Knowledge Search Intent", ContentEnum.STATE, "start",
                                     user_id)
            state_machine.handle_knowledge_search()
            await response_websocket(websocket, session_id, "Knowledge Search Intent", ContentEnum.STATE, "end",
                                     user_id)
        elif state_machine.get_state() == QueryState.ENTITY_RETRIEVAL:
            await response_websocket(websocket, session_id, "Entity Info Retrieval", ContentEnum.STATE, "start",
                                     user_id)
            state_machine.handle_entity_retrieval()
            await response_websocket(websocket, session_id, "Entity Info Retrieval", ContentEnum.STATE, "end",
                                     user_id)
        elif state_machine.get_state() == QueryState.QA_RETRIEVAL:
            await response_websocket(websocket, session_id, "QA Info Retrieval", ContentEnum.STATE, "start",
                                     user_id)
            state_machine.handle_qa_retrieval()
            await response_websocket(websocket, session_id, "QA Info Retrieval", ContentEnum.STATE, "end",
                                     user_id)
        elif state_machine.get_state() == QueryState.SQL_GENERATION:
            await response_websocket(websocket, session_id, "Generating SQL", ContentEnum.STATE, "start", user_id)
            state_machine.handle_sql_generation()
            await response_websocket(websocket, session_id, "Generating SQL", ContentEnum.STATE, "end", user_id)
        elif state_machine.get_state() == QueryState.INTENT_RECOGNITION:
            await response_websocket(websocket, session_id, "Query Intent Analyse", ContentEnum.STATE, "start", user_id)
            state_machine.handle_intent_recognition()
            await response_websocket(websocket, session_id, "Query Intent Analyse", ContentEnum.STATE, "end", user_id)
        elif state_machine.get_state() == QueryState.EXECUTE_QUERY:
            await response_websocket(websocket, session_id, "Database SQL Execution", ContentEnum.STATE, "start",
                                     user_id)
            state_machine.handle_execute_query()
            await response_websocket(websocket, session_id, "Database SQL Execution", ContentEnum.STATE, "end",
                                     user_id)
        elif state_machine.get_state() == QueryState.ANALYZE_DATA:
            await response_websocket(websocket, session_id, "Generating Data Insights", ContentEnum.STATE,
                                     "start", user_id)
            state_machine.handle_analyze_data()
            await response_websocket(websocket, session_id, "Generating Data Insights", ContentEnum.STATE,
                                     "end", user_id)
        elif state_machine.get_state() == QueryState.ASK_ENTITY_SELECT:
            state_machine.handle_entity_selection()
        elif state_machine.get_state() == QueryState.AGENT_TASK:
            await response_websocket(websocket, session_id, "Agent Task Split", ContentEnum.STATE,
                                     "start", user_id)
            state_machine.handle_agent_task()
            await response_websocket(websocket, session_id, "Agent Task Split", ContentEnum.STATE,
                                     "end", user_id)
        elif state_machine.get_state() == QueryState.AGENT_SEARCH:
            await response_websocket(websocket, session_id, "Agent SQL Generating", ContentEnum.STATE,
                                     "start", user_id)
            state_machine.handle_agent_sql_generation()
            await response_websocket(websocket, session_id, "Agent SQL Generating", ContentEnum.STATE,
                                     "end", user_id)
        elif state_machine.get_state() == QueryState.AGENT_DATA_SUMMARY:
            await response_websocket(websocket, session_id, "Generating Data Insights", ContentEnum.STATE,
                                     "start", user_id)
            state_machine.handle_agent_analyze_data()
            await response_websocket(websocket, session_id, "Generating Data Insights", ContentEnum.STATE,
                                     "end", user_id)
        elif state_machine.get_state() == QueryState.USER_SELECT_ENTITY:
            await response_websocket(websocket, session_id, "User Entity Select", ContentEnum.STATE,
                                     "start", user_id)
            state_machine.handle_user_select_entity()
            await response_websocket(websocket, session_id, "User Entity Select", ContentEnum.STATE,
                                     "end", user_id)
        else:
            state_machine.state = QueryState.ERROR

    if processing_context.gen_suggested_question_flag and state_machine.get_answer().query_intent != "entity_select":
        if state_machine.search_intent_flag or state_machine.agent_intent_flag:
            await response_websocket(websocket, session_id, "Generating Suggested Questions", ContentEnum.STATE,
                                     "start", user_id)
            state_machine.handle_suggest_question()
            await response_websocket(websocket, session_id, "Generating Suggested Questions", ContentEnum.STATE,
                                     "end", user_id)

    if state_machine.get_state() == QueryState.COMPLETE:
        await response_websocket(websocket, session_id, "Data Visualization", ContentEnum.STATE,
                                 "start", user_id)
        state_machine.handle_data_visualization()
        await response_websocket(websocket, session_id, "Data Visualization", ContentEnum.STATE,
                                 "end", user_id)
        state_machine.handle_add_to_log(log_id=log_id)

    return state_machine.get_answer()


def user_feedback_upvote(data_profiles: str, user_id: str, session_id: str, query: str, query_intent: str,
                         query_answer):
    try:
        if query_intent == "normal_search":
            VectorStore.add_sample(data_profiles, query, query_answer)
        elif query_intent == "agent_search":
            VectorStore.add_sample(data_profiles, query, query_answer)
            # VectorStore.add_agent_cot_sample(data_profiles, query, "\n".join(query_list))
        return True
    except Exception as e:
        return False


def user_feedback_downvote(data_profiles: str, user_id: str, session_id: str, query: str, query_intent: str,
                           query_answer, error_description="", error_categories="", correct_sql_reference=""):
    try:
        error_info_dict = {
            "error_description": error_description,
            "error_categories": error_categories,
            "correct_sql_reference": correct_sql_reference
        }
        error_info = json.dumps(error_info_dict, ensure_ascii=False)
        if query_intent == "normal_search":
            log_id = generate_log_id()
            current_time = get_current_time()
            FeedBackManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                              profile_name=data_profiles,
                                              sql=query_answer, query=query,
                                              intent="normal_search_user_downvote",
                                              log_info=error_info,
                                              time_str=current_time,
                                              log_type="feedback_downvote")
        elif query_intent == "agent_search":
            log_id = generate_log_id()
            current_time = get_current_time()
            FeedBackManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                              profile_name=data_profiles,
                                              sql=query_answer, query=query,
                                              intent="agent_search_user_downvote",
                                              log_info=error_info,
                                              time_str=current_time,
                                              log_type="feedback_downvote")
        return True
    except Exception as e:
        return False


def ask_with_response_stream(question: Question, current_nlq_chain: NLQChain) -> dict:
    logger.info('try to get generated sql from LLM')
    response = get_result_from_llm(question, current_nlq_chain, True)
    logger.info("got llm response")
    return response


def get_executed_result(current_nlq_chain: NLQChain) -> str:
    all_profiles = ProfileManagement.get_all_profiles_with_info()
    sql_query_result = current_nlq_chain.get_executed_result_df(all_profiles[current_nlq_chain.profile])
    final_sql_query_result = sql_query_result.to_markdown()
    return final_sql_query_result


async def normal_text_search_websocket(websocket: WebSocket, session_id: str, search_box, model_type, database_profile,
                                       entity_slot, opensearch_info, selected_profile, use_rag, user_id,
                                       model_provider=None, username=None):
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
            # TODO: db_type already set in profile
            database_profile['db_type'] = ConnectionManagement.get_db_type_by_name(conn_name)

        if len(entity_slot) > 0 and use_rag:
            await response_websocket(websocket, session_id, "Entity Info Retrieval", ContentEnum.STATE, "start",
                                     user_id)
            for each_entity in entity_slot:
                entity_retrieve = get_retrieve_opensearch(opensearch_info, each_entity, "ner",
                                                          selected_profile, 1, 0.7)
                if len(entity_retrieve) > 0:
                    entity_slot_retrieve.extend(entity_retrieve)
            await response_websocket(websocket, session_id, "Entity Info Retrieval", ContentEnum.STATE, "end", user_id)

        if use_rag:
            await response_websocket(websocket, session_id, "QA Info Retrieval", ContentEnum.STATE, "start", user_id)
            retrieve_result = get_retrieve_opensearch(opensearch_info, search_box, "query",
                                                      selected_profile, 3, 0.5)
            await response_websocket(websocket, session_id, "QA Info Retrieval", ContentEnum.STATE, "end", user_id)

        await response_websocket(websocket, session_id, "Generating SQL", ContentEnum.STATE, "start", user_id)

        response = text_to_sql(database_profile['tables_info'],
                               database_profile['hints'],
                               database_profile['prompt_map'],
                               search_box,
                               model_id=model_type,
                               sql_examples=retrieve_result,
                               ner_example=entity_slot_retrieve,
                               dialect=database_profile['db_type'],
                               model_provider=model_provider)
        logger.info(f'{response=}')
        await response_websocket(websocket, session_id, "Generating SQL", ContentEnum.STATE, "end", user_id)
        sql = get_generated_sql(response)
        # post-processing the sql for row level security
        post_sql = DataSourceFactory.apply_row_level_security_for_sql(
                        database_profile['db_type'],
                        sql,
                        database_profile['row_level_security_config'],
                        username
                    )

        search_result = SearchTextSqlResult(search_query=search_box, entity_slot_retrieve=entity_slot_retrieve,
                                            retrieve_result=retrieve_result, response=response, sql="")
        search_result.entity_slot_retrieve = entity_slot_retrieve
        search_result.retrieve_result = retrieve_result
        search_result.response = response
        search_result.sql = post_sql
        search_result.original_sql = sql
    except Exception as e:
        logger.exception(e)
    return search_result


async def normal_sql_regenerating_websocket(websocket: WebSocket, session_id: str, search_box, model_type,
                                            database_profile, entity_slot_retrieve, retrieve_result, additional_info,
                                            username: str):
    entity_slot_retrieve = entity_slot_retrieve
    retrieve_result = retrieve_result
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

        response = text_to_sql(database_profile['tables_info'],
                               database_profile['hints'],
                               database_profile['prompt_map'],
                               search_box,
                               model_id=model_type,
                               sql_examples=retrieve_result,
                               ner_example=entity_slot_retrieve,
                               dialect=database_profile['db_type'],
                               model_provider=None,
                               additional_info=additional_info)
        logger.info("normal_sql_regenerating_websocket")
        logger.info(f'{response=}')
        sql = get_generated_sql(response)
        post_sql = DataSourceFactory.apply_row_level_security_for_sql(
                        database_profile['db_type'],
                        sql,
                        database_profile['row_level_security_config'],
                        username
                    )
        search_result = SearchTextSqlResult(search_query=search_box, entity_slot_retrieve=entity_slot_retrieve,
                                            retrieve_result=retrieve_result, response=response, sql="")
        search_result.entity_slot_retrieve = entity_slot_retrieve
        search_result.retrieve_result = retrieve_result
        search_result.response = response
        search_result.sql = post_sql
        search_result.original_sql = sql
    except Exception as e:
        logger.error(e)
    return search_result


async def response_websocket(websocket: WebSocket, session_id: str, content,
                             content_type: ContentEnum = ContentEnum.COMMON, status: str = "-1",
                             user_id: str = "admin"):
    if content_type == ContentEnum.STATE:
        content_json = {
            "text": content,
            "status": status
        }
        content = content_json

    content_obj = {
        "session_id": session_id,
        "user_id": user_id,
        "content_type": content_type.value,
        "content": content,
    }
    logger.info(content_obj)
    final_content = json.dumps(content_obj, default=serialize_timestamp)
    await websocket.send_text(final_content)
