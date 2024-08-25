import json
import os
from typing import Union
from dotenv import load_dotenv

from nlq.business.connection import ConnectionManagement
from nlq.business.datasource.factory import DataSourceFactory
from nlq.business.model import ModelManagement
from nlq.business.nlq_chain import NLQChain
from nlq.business.profile import ProfileManagement
from nlq.business.vector_store import VectorStore
from nlq.business.log_store import LogManagement
from utils.apis import get_sql_result_tool
from utils.database import get_db_url_dialect
from nlq.business.suggested_question import SuggestedQuestionManagement as sqm
from utils.domain import SearchTextSqlResult
from utils.llm import text_to_sql, get_query_intent, knowledge_search, get_agent_cot_task, \
    data_analyse_tool, generate_suggested_question, data_visualization, get_query_rewrite
from utils.logging import getLogger
from utils.opensearch import get_retrieve_opensearch
from utils.env_var import opensearch_info
from utils.text_search import normal_text_search, agent_text_search
from utils.tool import generate_log_id, get_current_time, get_generated_sql_explain, get_generated_sql, \
    change_class_to_str
from .schemas import Question, Answer, Example, Option, SQLSearchResult, AgentSearchResult, KnowledgeSearchResult, \
    TaskSQLSearchResult, ChartEntity, AskReplayResult, ChatHistory, Message, HistoryMessage, AskEntitySelect
from .exception_handler import BizException
from utils.constant import BEDROCK_MODEL_IDS, ACTIVE_PROMPT_NAME
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


def ask(question: Question) -> Answer:
    logger.debug(question)
    verify_parameters(question)
    user_id = question.user_id
    session_id = question.session_id

    intent_ner_recognition_flag = question.intent_ner_recognition_flag
    agent_cot_flag = question.agent_cot_flag

    model_type = question.bedrock_model_id
    search_box = question.query
    selected_profile = question.profile_name
    use_rag_flag = question.use_rag_flag
    explain_gen_process_flag = question.explain_gen_process_flag
    gen_suggested_question_flag = question.gen_suggested_question_flag
    answer_with_insights = question.answer_with_insights

    reject_intent_flag = False
    search_intent_flag = False
    agent_intent_flag = False
    knowledge_search_flag = False

    agent_search_result = []
    normal_search_result = None

    filter_deep_dive_sql_result = []

    log_id = generate_log_id()
    current_time = get_current_time()
    log_info = ""

    all_profiles = ProfileManagement.get_all_profiles_with_info()
    if selected_profile not in all_profiles:
        raise BizException(ErrorEnum.PROFILE_NOT_FOUND)
    database_profile = all_profiles[selected_profile]

    current_nlq_chain = NLQChain(selected_profile)

    sql_chart_data = ChartEntity(chart_type="", chart_data=[])

    sql_search_result = SQLSearchResult(sql_data=[], sql="", data_show_type="table",
                                        sql_gen_process="",
                                        data_analyse="", sql_data_chart=[])

    agent_search_response = AgentSearchResult(agent_summary="", agent_sql_search_result=[])

    knowledge_search_result = KnowledgeSearchResult(knowledge_response="")

    agent_sql_search_result = []

    generate_suggested_question_list = []

    if database_profile['db_url'] == '':
        conn_name = database_profile['conn_name']
        db_url = ConnectionManagement.get_db_url_by_name(conn_name)
        database_profile['db_url'] = db_url
        database_profile['db_type'] = ConnectionManagement.get_db_type_by_name(conn_name)
    prompt_map = database_profile['prompt_map']

    entity_slot = []

    if intent_ner_recognition_flag:
        intent_response = get_query_intent(model_type, search_box, prompt_map)
        intent = intent_response.get("intent", "normal_search")
        entity_slot = intent_response.get("slot", [])
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

    if reject_intent_flag:
        answer = Answer(query=search_box, query_intent="reject_search", knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=[])
        LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                          profile_name=selected_profile, sql="", query=search_box,
                                          intent="reject_search", log_info="", time_str=current_time)
        return answer
    elif search_intent_flag:
        normal_search_result = normal_text_search(search_box, model_type,
                                                  database_profile,
                                                  entity_slot, opensearch_info,
                                                  selected_profile, use_rag_flag)
    elif knowledge_search_flag:
        response = knowledge_search(search_box=search_box, model_id=model_type, prompt_map=prompt_map)

        knowledge_search_result.knowledge_response = response
        answer = Answer(query=search_box, query_intent="knowledge_search",
                        knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=[])

        LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                          profile_name=selected_profile, sql="", query=search_box,
                                          intent="knowledge_search",
                                          log_info=knowledge_search_result.knowledge_response,
                                          time_str=current_time)
        return answer

    else:
        agent_cot_retrieve = get_retrieve_opensearch(opensearch_info, search_box, "agent",
                                                     selected_profile, 2, 0.5)
        agent_cot_task_result = get_agent_cot_task(model_type, prompt_map, search_box,
                                                   database_profile['tables_info'],
                                                   agent_cot_retrieve)

        agent_search_result = agent_text_search(search_box, model_type,
                                                database_profile,
                                                entity_slot, opensearch_info,
                                                selected_profile, use_rag_flag, agent_cot_task_result)

    if gen_suggested_question_flag and (search_intent_flag or agent_intent_flag):
        active_prompt = sqm.get_prompt_by_name(ACTIVE_PROMPT_NAME).prompt
        generated_sq = generate_suggested_question(prompt_map, search_box, model_id=model_type)
        split_strings = generated_sq.split("[generate]")
        generate_suggested_question_list = [s.strip() for s in split_strings if s.strip()]

    if search_intent_flag:
        if normal_search_result.sql != "":
            current_nlq_chain.set_generated_sql(normal_search_result.sql)
            sql_search_result.sql = normal_search_result.sql.strip()
            current_nlq_chain.set_generated_sql_response(normal_search_result.response)
            if explain_gen_process_flag:
                sql_search_result.sql_gen_process = current_nlq_chain.get_generated_sql_explain().strip()
        else:
            sql_search_result.sql = "-1"

        search_intent_result = get_sql_result_tool(database_profile,
                                                   current_nlq_chain.get_generated_sql())
        if search_intent_result["status_code"] == 500:
            sql_search_result.data_analyse = "The query results are temporarily unavailable, please switch to debugging webpage to try the same query and check the log file for more information."
        else:
            if search_intent_result["data"] is not None and len(search_intent_result["data"]) > 0:
                if answer_with_insights:
                    search_intent_result["data"] = search_intent_result["data"].fillna("")
                    search_intent_analyse_result = data_analyse_tool(model_type, prompt_map, search_box,
                                                                     search_intent_result["data"].to_json(
                                                                         orient='records', force_ascii=False), "query")

                    sql_search_result.data_analyse = search_intent_analyse_result

                model_select_type, show_select_data, select_chart_type, show_chart_data = data_visualization(model_type,
                                                                                                             search_box,
                                                                                                             search_intent_result[
                                                                                                                 "data"],
                                                                                                             database_profile[
                                                                                                                 'prompt_map'])

                if select_chart_type != "-1":
                    sql_chart_data = ChartEntity(chart_type="", chart_data=[])
                    sql_chart_data.chart_type = select_chart_type
                    sql_chart_data.chart_data = show_chart_data
                    sql_search_result.sql_data_chart = [sql_chart_data]

                sql_search_result.sql_data = show_select_data
                sql_search_result.data_show_type = model_select_type

        log_info = str(search_intent_result["error_info"]) + ";" + sql_search_result.data_analyse
        LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                          profile_name=selected_profile, sql=sql_search_result.sql,
                                          query=search_box,
                                          intent="normal_search",
                                          log_info=log_info,
                                          time_str=current_time)
        answer = Answer(query=search_box, query_intent="normal_search", knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=generate_suggested_question_list)
        return answer
    else:
        sub_search_task = []
        for i in range(len(agent_search_result)):
            each_task_res = get_sql_result_tool(database_profile, agent_search_result[i]["sql"])
            if each_task_res["status_code"] == 200 and len(each_task_res["data"]) > 0:
                agent_search_result[i]["data_result"] = each_task_res["data"].to_json(
                    orient='records')
                filter_deep_dive_sql_result.append(agent_search_result[i])
                each_task_sql_res = [list(each_task_res["data"].columns)] + each_task_res["data"].values.tolist()

                model_select_type, show_select_data, select_chart_type, show_chart_data = data_visualization(model_type,
                                                                                                             agent_search_result[
                                                                                                                 i][
                                                                                                                 "query"],
                                                                                                             each_task_res[
                                                                                                                 "data"],
                                                                                                             database_profile[
                                                                                                                 'prompt_map'])

                each_task_sql_response = get_generated_sql_explain(agent_search_result[i]["response"])
                sub_task_sql_result = SQLSearchResult(sql_data=show_select_data, sql=each_task_res["sql"],
                                                      data_show_type=model_select_type,
                                                      sql_gen_process=each_task_sql_response,
                                                      data_analyse="", sql_data_chart=[])
                if select_chart_type != "-1":
                    sub_sql_chart_data = ChartEntity(chart_type="", chart_data=[])
                    sub_sql_chart_data.chart_type = select_chart_type
                    sub_sql_chart_data.chart_data = show_chart_data
                    sub_task_sql_result.sql_data_chart = [sub_sql_chart_data]

                each_task_sql_search_result = TaskSQLSearchResult(sub_task_query=agent_search_result[i]["query"],
                                                                  sql_search_result=sub_task_sql_result)
                agent_sql_search_result.append(each_task_sql_search_result)

                sub_search_task.append(agent_search_result[i]["query"])
                log_info = ""
            else:
                log_info = agent_search_result[i]["query"] + "The SQL error Info: "
            log_id = generate_log_id()
            LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                              profile_name=selected_profile, sql=each_task_res["sql"],
                                              query=search_box + "; The sub task is " + agent_search_result[i]["query"],
                                              intent="agent_search",
                                              log_info=log_info,
                                              time_str=current_time)
        agent_data_analyse_result = data_analyse_tool(model_type, prompt_map, search_box,
                                                      json.dumps(filter_deep_dive_sql_result, ensure_ascii=False),
                                                      "agent")
        logger.info("agent_data_analyse_result")
        logger.info(agent_data_analyse_result)
        agent_search_response.agent_summary = agent_data_analyse_result
        agent_search_response.agent_sql_search_result = agent_sql_search_result

        answer = Answer(query=search_box, query_intent="agent_search", knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=generate_suggested_question_list)
        return answer


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

    reject_intent_flag = False
    search_intent_flag = False
    agent_intent_flag = False
    knowledge_search_flag = False
    ask_replay_flag = False

    agent_search_result = []
    normal_search_result = None

    filter_deep_dive_sql_result = []

    log_id = generate_log_id()
    current_time = get_current_time()
    log_info = ""
    query_rewrite = ""

    all_profiles = ProfileManagement.get_all_profiles_with_info()
    database_profile = all_profiles[selected_profile]

    current_nlq_chain = NLQChain(selected_profile)

    sql_chart_data = ChartEntity(chart_type="", chart_data=[])

    ask_result = AskReplayResult(query_rewrite="")

    sql_search_result = SQLSearchResult(sql_data=[], sql="", data_show_type="table",
                                        sql_gen_process="",
                                        data_analyse="", sql_data_chart=[])

    agent_search_response = AgentSearchResult(agent_summary="", agent_sql_search_result=[])

    knowledge_search_result = KnowledgeSearchResult(knowledge_response="")

    ask_entity_select = AskEntitySelect(entity_select="", entity_info={})

    agent_sql_search_result = []

    generate_suggested_question_list = []

    if database_profile['db_url'] == '':
        conn_name = database_profile['conn_name']
        db_url = ConnectionManagement.get_db_url_by_name(conn_name)
        database_profile['db_url'] = db_url
        database_profile['db_type'] = ConnectionManagement.get_db_type_by_name(conn_name)
    prompt_map = database_profile['prompt_map']

    entity_slot = []

    query_rewrite_result = {"intent": "original_problem", "query": search_box}
    if context_window > 0:
        user_query_history = LogManagement.get_history_by_session(profile_name=selected_profile, user_id=user_id,
                                                                  session_id=session_id, size=context_window,
                                                                  log_type='chat_history')
        if len(user_query_history) >= 0:
            user_query_history.append("user:" + search_box)
            logger.info("The Chat history is {history}".format(history="\n".join(user_query_history)))
            query_rewrite_result = get_query_rewrite(model_type, search_box, prompt_map, user_query_history)
            logger.info(
                "The query_rewrite_result is {query_rewrite_result}".format(query_rewrite_result=query_rewrite_result))
    query_rewrite = query_rewrite_result.get("query")
    query_rewrite_intent = query_rewrite_result.get("intent")
    if "ask_in_reply" == query_rewrite_intent:
        ask_replay_flag = True

    if ask_replay_flag:
        ask_result.query_rewrite = query_rewrite_result.get("query")

        answer = Answer(query=search_box, query_rewrite=ask_result.query_rewrite, query_intent="ask_in_reply", knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=[], ask_rewrite_result=ask_result, ask_entity_select=ask_entity_select)

        ask_answer_info = change_class_to_str(answer)
        LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                          profile_name=selected_profile, sql="", query=search_box,
                                          intent="ask_in_reply",
                                          log_info=ask_answer_info,
                                          log_type="chat_history",
                                          time_str=current_time)
        return answer

    if intent_ner_recognition_flag:
        await response_websocket(websocket, session_id, "Query Intent Analyse", ContentEnum.STATE, "start", user_id)
        intent_response = get_query_intent(model_type, query_rewrite, prompt_map)
        await response_websocket(websocket, session_id, "Query Intent Analyse", ContentEnum.STATE, "end", user_id)
        intent = intent_response.get("intent", "normal_search")
        entity_slot = intent_response.get("slot", [])
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

    if reject_intent_flag:
        answer = Answer(query=search_box, query_rewrite=query_rewrite, query_intent="reject_search", knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=[], ask_rewrite_result=ask_result, ask_entity_select=ask_entity_select)
        reject_answer_info = change_class_to_str(answer)
        LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                          profile_name=selected_profile, sql="", query=search_box,
                                          intent="reject_search", log_info=reject_answer_info, log_type="chat_history",
                                          time_str=current_time)
        return answer
    elif search_intent_flag:
        normal_search_result = await normal_text_search_websocket(websocket, session_id, query_rewrite, model_type,
                                                                  database_profile,
                                                                  entity_slot, opensearch_info,
                                                                  selected_profile, use_rag_flag, user_id,
                                                                  username=username)
    elif knowledge_search_flag:
        response = knowledge_search(search_box=search_box, model_id=model_type, prompt_map=prompt_map)

        knowledge_search_result.knowledge_response = response
        answer = Answer(query=search_box, query_rewrite=query_rewrite, query_intent="knowledge_search",
                        knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=[], ask_rewrite_result=ask_result, ask_entity_select=ask_entity_select)
        knowledge_answer_info = change_class_to_str(answer)
        LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                          profile_name=selected_profile, sql="", query=search_box,
                                          intent="knowledge_search",
                                          log_info=knowledge_answer_info,
                                          log_type="chat_history",
                                          time_str=current_time)
        return answer

    else:
        agent_cot_retrieve = get_retrieve_opensearch(opensearch_info, query_rewrite, "agent",
                                                     selected_profile, 2, 0.5)
        agent_cot_task_result = get_agent_cot_task(model_type, prompt_map, query_rewrite,
                                                   database_profile['tables_info'],
                                                   agent_cot_retrieve)

        agent_search_result = agent_text_search(query_rewrite, model_type,
                                                database_profile,
                                                entity_slot, opensearch_info,
                                                selected_profile, use_rag_flag, agent_cot_task_result)

    if gen_suggested_question_flag and (search_intent_flag or agent_intent_flag):
        active_prompt = sqm.get_prompt_by_name(ACTIVE_PROMPT_NAME).prompt
        generated_sq = generate_suggested_question(prompt_map, query_rewrite, model_id=model_type)
        split_strings = generated_sq.split("[generate]")
        generate_suggested_question_list = [s.strip() for s in split_strings if s.strip()]

    if search_intent_flag:
        if normal_search_result.sql != "":
            current_nlq_chain.set_generated_sql(normal_search_result.sql)
            sql_search_result.sql = normal_search_result.sql.strip()
            current_nlq_chain.set_generated_sql_response(normal_search_result.response)
            if explain_gen_process_flag:
                sql_search_result.sql_gen_process = current_nlq_chain.get_generated_sql_explain().strip()
        else:
            sql_search_result.sql = "-1"

        await response_websocket(websocket, session_id, "Database SQL Execution", ContentEnum.STATE, "start", user_id)

        search_intent_result = get_sql_result_tool(database_profile,
                                                   current_nlq_chain.get_generated_sql())

        await response_websocket(websocket, session_id, "Database SQL Execution", ContentEnum.STATE, "end", user_id)

        if search_intent_result["status_code"] == 500:
            await response_websocket(websocket, session_id, "Regenerating SQL ", ContentEnum.STATE, "start", user_id)

            additional_info = '''\n NOTE: when I try to write a SQL <sql>{sql_statement}</sql>, I got an error <error>{error}</error>. Please consider and avoid this problem. '''.format(
                sql_statement=normal_search_result.original_sql,
                error=search_intent_result["error_info"])
            normal_search_result = await normal_sql_regenerating_websocket(websocket=websocket, session_id=session_id, search_box=query_rewrite,
                                              model_type=model_type, database_profile=database_profile,
                                              entity_slot_retrieve=normal_search_result.entity_slot_retrieve,
                                              retrieve_result=normal_search_result.retrieve_result, additional_info=additional_info,
                                              username=username)

            await response_websocket(websocket, session_id, "Regenerating SQL ", ContentEnum.STATE, "start", user_id)
            if normal_search_result.sql != "":
                current_nlq_chain.set_generated_sql(normal_search_result.sql)
                sql_search_result.sql = normal_search_result.sql.strip()
                current_nlq_chain.set_generated_sql_response(normal_search_result.response)
                if explain_gen_process_flag:
                    sql_search_result.sql_gen_process = current_nlq_chain.get_generated_sql_explain().strip()
            else:
                sql_search_result.sql = "-1"
        await response_websocket(websocket, session_id, "Database SQL Execution", ContentEnum.STATE, "start", user_id)
        search_intent_result = get_sql_result_tool(database_profile,
                                                   current_nlq_chain.get_generated_sql())
        await response_websocket(websocket, session_id, "Database SQL Execution", ContentEnum.STATE, "end", user_id)
        if search_intent_result["status_code"] == 500:
            sql_search_result.data_analyse = "The query results are temporarily unavailable, please switch to debugging webpage to try the same query and check the log file for more information."
        else:
            if search_intent_result["data"] is not None and len(search_intent_result["data"]) > 0:
                search_intent_result["data"] = search_intent_result["data"].fillna("")
                if answer_with_insights:
                    await response_websocket(websocket, session_id, "Generating Data Insights", ContentEnum.STATE,
                                             "start", user_id)
                    search_intent_analyse_result = data_analyse_tool(model_type, prompt_map, query_rewrite,
                                                                     search_intent_result["data"].to_json(
                                                                         orient='records', force_ascii=False), "query")

                    await response_websocket(websocket, session_id, "Generating Data Insights", ContentEnum.STATE,
                                             "end", user_id)

                    sql_search_result.data_analyse = search_intent_analyse_result

                await response_websocket(websocket, session_id, "Data Visualization", ContentEnum.STATE, "start",
                                         user_id)
                model_select_type, show_select_data, select_chart_type, show_chart_data = data_visualization(model_type,
                                                                                                             query_rewrite,
                                                                                                             search_intent_result[
                                                                                                                 "data"],
                                                                                                             database_profile[
                                                                                                                 'prompt_map'])
                await response_websocket(websocket, session_id, "Data Visualization", ContentEnum.STATE, "end", user_id)

                if select_chart_type != "-1":
                    sql_chart_data = ChartEntity(chart_type="", chart_data=[])
                    sql_chart_data.chart_type = select_chart_type
                    sql_chart_data.chart_data = show_chart_data
                    sql_search_result.sql_data_chart = [sql_chart_data]

                sql_search_result.sql_data = show_select_data
                sql_search_result.data_show_type = model_select_type

        log_info = str(search_intent_result["error_info"]) + ";" + sql_search_result.data_analyse
        LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                          profile_name=selected_profile, sql=sql_search_result.sql,
                                          query=search_box,
                                          intent="normal_search",
                                          log_info=log_info,
                                          log_type="normal_log",
                                          time_str=current_time)
        answer = Answer(query=search_box, query_rewrite=query_rewrite, query_intent="normal_search", knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=generate_suggested_question_list, ask_rewrite_result=ask_result, ask_entity_select=ask_entity_select)
        intent_answer_info = change_class_to_str(answer)
        LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                          profile_name=selected_profile, sql=sql_search_result.sql,
                                          query=search_box,
                                          intent="normal_search",
                                          log_info=intent_answer_info,
                                          log_type="chat_history",
                                          time_str=current_time)
        return answer
    else:
        sub_search_task = []
        for i in range(len(agent_search_result)):
            each_task_res = get_sql_result_tool(database_profile, agent_search_result[i]["sql"])
            if each_task_res["status_code"] == 200 and len(each_task_res["data"]) > 0:
                agent_search_result[i]["data_result"] = each_task_res["data"].to_json(
                    orient='records')
                filter_deep_dive_sql_result.append(agent_search_result[i])
                each_task_sql_res = [list(each_task_res["data"].columns)] + each_task_res["data"].values.tolist()

                model_select_type, show_select_data, select_chart_type, show_chart_data = data_visualization(model_type,
                                                                                                             agent_search_result[
                                                                                                                 i][
                                                                                                                 "query"],
                                                                                                             each_task_res[
                                                                                                                 "data"],
                                                                                                             database_profile[
                                                                                                                 'prompt_map'])

                each_task_sql_response = get_generated_sql_explain(agent_search_result[i]["response"])
                sub_task_sql_result = SQLSearchResult(sql_data=show_select_data, sql=each_task_res["sql"],
                                                      data_show_type=model_select_type,
                                                      sql_gen_process=each_task_sql_response,
                                                      data_analyse="", sql_data_chart=[])
                if select_chart_type != "-1":
                    sub_sql_chart_data = ChartEntity(chart_type="", chart_data=[])
                    sub_sql_chart_data.chart_type = select_chart_type
                    sub_sql_chart_data.chart_data = show_chart_data
                    sub_task_sql_result.sql_data_chart = [sub_sql_chart_data]

                each_task_sql_search_result = TaskSQLSearchResult(sub_task_query=agent_search_result[i]["query"],
                                                                  sql_search_result=sub_task_sql_result)
                agent_sql_search_result.append(each_task_sql_search_result)

                sub_search_task.append(agent_search_result[i]["query"])
                log_info = ""
            else:
                log_info = agent_search_result[i]["query"] + "The SQL error Info: "
            log_id = generate_log_id()
            LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                              profile_name=selected_profile, sql=each_task_res["sql"],
                                              query=search_box + "; The sub task is " + agent_search_result[i]["query"],
                                              intent="agent_search",
                                              log_info=log_info,
                                              time_str=current_time)
        agent_data_analyse_result = data_analyse_tool(model_type, prompt_map, query_rewrite,
                                                      json.dumps(filter_deep_dive_sql_result, ensure_ascii=False),
                                                      "agent")
        logger.info("agent_data_analyse_result")
        logger.info(agent_data_analyse_result)
        agent_search_response.agent_summary = agent_data_analyse_result
        agent_search_response.agent_sql_search_result = agent_sql_search_result

        answer = Answer(query=search_box, query_rewrite=query_rewrite, query_intent="agent_search", knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=generate_suggested_question_list, ask_rewrite_result=ask_result, ask_entity_select=ask_entity_select)
        agent_answer_info = change_class_to_str(answer)
        LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                          profile_name=selected_profile, sql="",
                                          query=search_box,
                                          intent="agent_search",
                                          log_info=agent_answer_info,
                                          log_type="chat_history",
                                          time_str=current_time)
        return answer


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
                           query_answer):
    try:
        if query_intent == "normal_search":
            log_id = generate_log_id()
            current_time = get_current_time()
            LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                              profile_name=data_profiles,
                                              sql=query_answer, query=query,
                                              intent="normal_search_user_downvote",
                                              log_info="",
                                              time_str=current_time,
                                              log_type="feedback_downvote")
        elif query_intent == "agent_search":
            log_id = generate_log_id()
            current_time = get_current_time()
            LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                              profile_name=data_profiles,
                                              sql=query_answer, query=query,
                                              intent="agent_search_user_downvote",
                                              log_info="",
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
    final_content = json.dumps(content_obj)
    await websocket.send_text(final_content)
