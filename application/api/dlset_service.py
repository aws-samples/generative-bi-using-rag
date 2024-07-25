# -*- coding:utf-8 -*-
# @FileName  : dlset_service.py
# @Time      : 2024/7/19 15:49
# @Author    : dingtianlu
# @Function  :
import json
import logging
import os

from fastapi import WebSocket
from nlq.business.connection import ConnectionManagement
from nlq.business.nlq_chain import NLQChain
from nlq.business.profile import ProfileManagement
from nlq.business.log_store import LogManagement
from utils.apis import get_sql_result_tool
from nlq.business.suggested_question import SuggestedQuestionManagement as sqm
from utils.domain import SearchTextSqlResult, SearchTextJsonResult
from utils.llm import get_query_intent, knowledge_search, get_agent_cot_task, data_analyse_tool, \
    generate_suggested_question, data_visualization, text_to_json, get_query_rewrite
from utils.opensearch import get_retrieve_opensearch
from utils.env_var import opensearch_info
from utils.text_search import agent_text_search
from utils.tool import generate_log_id, get_current_time, get_generated_sql_explain, get_generated_json, \
    get_generated_think
from .schemas import SupersetAnswer, SQLSearchResult, AgentSearchResult, KnowledgeSearchResult, \
    TaskSQLSearchResult, ChartEntity, DlsetQuestion, JSONSearchResult
from utils.constant import ACTIVE_PROMPT_NAME
from .enum import ContentEnum
import sqlalchemy as db

logger = logging.getLogger(__name__)


def execute_sql(sql):
    engine = db.create_engine(os.getenv("SUPERSET_DATABASE_URI"))
    with engine.connect() as con:
        rs = con.execute(sql)
        data = [dict(zip(result.keys(), result)) for result in rs]
    return data


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


async def normal_text_search_websocket(websocket: WebSocket, session_id: str, search_box, model_type, database_profile,
                                       entity_slot, opensearch_info, selected_profile, use_rag, user_id, table_id,
                                       model_provider=None):
    entity_slot_retrieve = []
    retrieve_result = []
    response = ""
    search_result = SearchTextJsonResult(search_query=search_box, entity_slot_retrieve=entity_slot_retrieve,
                                        retrieve_result=retrieve_result, response=response, json="", process_think="")
    try:
        if database_profile['db_url'] == '':
            conn_name = database_profile['conn_name']
            db_url = ConnectionManagement.get_db_url_by_name(conn_name)
            database_profile['db_url'] = db_url
            database_profile['db_type'] = ConnectionManagement.get_db_type_by_name(conn_name)

        if len(entity_slot) > 0 and use_rag:
            await response_websocket(websocket, session_id, "Entity Info Retrieval", ContentEnum.STATE, "start", user_id)
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

        await response_websocket(websocket, session_id, "Generating Chart Info", ContentEnum.STATE, "start", user_id)

        # 读取superset 数据集相关信息
        dataset_info_sql = f"""
        select column_name 字段,
         case when groupby=1 then '维度' else '度量' end as 维度度量,
         verbose_name verbose_name, filterable 是否可用于过滤, is_dttm 是否为时间列 from table_columns where table_id={table_id}"""

        dataset_info = execute_sql(dataset_info_sql)
        # 处理数据集信息 按照csv的格式处理
        dataset_info_csv = ["字段，维度度量，verbose_name，是否可用于过滤，是否为时间列"]
        for each_info in dataset_info:
            dataset_info_csv.append(f"        {each_info['字段']},{each_info['维度度量']},{each_info['verbose_name']},{each_info['是否可用于过滤']},{each_info['是否为时间列']}")
        dataset_info_csv = "\n".join(dataset_info_csv)

        table_info_sql = f"""
        select `schema`, table_name, description, main_dttm_col from tables where id={table_id}
        """
        table_info = execute_sql(table_info_sql)[0]

        # 读取数据集数据
        dataset_schema = f"""
        dataset_id: {table_id}
        dataset_name: {table_info['schema']}.{table_info['table_name']}
        dataset_description: {table_info['description']}
        主时间列: {table_info['main_dttm_col']}
        数据集列信息: 
        {dataset_info_csv}
        """

        response = text_to_json(
            dataset_schema,
            database_profile['tables_info'],
            database_profile['hints'],
            database_profile['prompt_map'],
            search_box,
            model_id=model_type,
            sql_examples=retrieve_result,
            ner_example=entity_slot_retrieve,
            dialect=database_profile['db_type'],
            model_provider=model_provider)
        logger.info(f'{response=}')
        await response_websocket(websocket, session_id, "Generating Chart Info", ContentEnum.STATE, "end", user_id)
        json_str = get_generated_json(response)
        think_process = get_generated_think(response)
        search_result = SearchTextJsonResult(search_query=search_box, entity_slot_retrieve=entity_slot_retrieve,
                                             retrieve_result=retrieve_result, response=response, json=json_str,
                                             process_think=think_process)
    except Exception as e:
        logger.error(e)
    return search_result


async def dlset_ask_websocket(websocket: WebSocket, question: DlsetQuestion):
    logger.info(question)
    session_id = question.session_id
    user_id = question.user_id
    intent_ner_recognition_flag = question.intent_ner_recognition_flag
    agent_cot_flag = question.agent_cot_flag
    model_type = question.bedrock_model_id
    search_box = question.query
    selected_profile = question.profile_name
    use_rag_flag = question.use_rag_flag
    gen_suggested_question_flag = question.gen_suggested_question_flag

    with_history = question.with_history
    context_windows = question.context_window
    table_id = question.table_id

    reject_intent_flag = False
    agent_intent_flag = False
    knowledge_search_flag = False

    log_id = generate_log_id()
    current_time = get_current_time()

    all_profiles = ProfileManagement.get_all_profiles_with_info()
    database_profile = all_profiles[selected_profile]

    json_search_result = JSONSearchResult(json="", think_process="")

    agent_search_response = AgentSearchResult(agent_summary="", agent_sql_search_result=[])

    knowledge_search_result = KnowledgeSearchResult(knowledge_response="")


    generate_suggested_question_list = []

    if database_profile['db_url'] == '':
        conn_name = database_profile['conn_name']
        db_url = ConnectionManagement.get_db_url_by_name(conn_name)
        database_profile['db_url'] = db_url
        database_profile['db_type'] = ConnectionManagement.get_db_type_by_name(conn_name)
    prompt_map = database_profile['prompt_map']
    entity_slot = []
    # 添加携带历史记录问题重写逻辑

    if with_history:
        # 获取历史问题
        if context_windows > 0:
            user_query_history = []
            user_history_questions = LogManagement.query_log_dao.get_logs(profile_name=selected_profile, user_id=user_id, session_id=session_id, size=context_windows, log_type='superset')
            for each_history_question in user_history_questions:
                user_query_history.append(each_history_question['query'])
            new_search_box = get_query_rewrite(model_type, search_box, prompt_map, user_query_history)
            search_box = new_search_box
    if intent_ner_recognition_flag:
        await response_websocket(websocket, session_id, "Query Intent Analyse", ContentEnum.STATE, "start", user_id)
        # 实体识别
        intent_response = get_query_intent(model_type, search_box, prompt_map)
        await response_websocket(websocket, session_id, "Query Intent Analyse", ContentEnum.STATE, "end",  user_id)
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
        # 拒绝搜索
        answer = SupersetAnswer(query=search_box, query_intent="reject_search",
                                knowledge_search_result=knowledge_search_result,
                                json_search_result=json_search_result, agent_search_result=agent_search_response,
                                suggested_question=[])
        LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                          profile_name=selected_profile, sql="", query=search_box,
                                          intent="reject_search", log_info="", time_str=current_time, log_type="superset")
        return answer
    elif search_intent_flag:
        # 普通搜索
        normal_search_result = await normal_text_search_websocket(websocket, session_id, search_box, model_type,
                                                                  database_profile,
                                                                  entity_slot, opensearch_info,
                                                                  selected_profile, use_rag_flag, user_id, table_id)
    elif knowledge_search_flag:
        # 知识搜索
        response = knowledge_search(search_box=search_box, model_id=model_type, prompt_map=prompt_map)

        knowledge_search_result.knowledge_response = response
        answer = SupersetAnswer(query=search_box, query_intent="knowledge_search",
                                knowledge_search_result=knowledge_search_result,
                                json_search_result=json_search_result, agent_search_result=agent_search_response,
                                suggested_question=[])

        LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                          profile_name=selected_profile, sql="", query=search_box,
                                          intent="knowledge_search",
                                          log_info=knowledge_search_result.knowledge_response,
                                          time_str=current_time, log_type="superset")
        return answer

    else:
        # cot
        # cot 不支持
        answer = SupersetAnswer(query=search_box, query_intent="agent_intent_flag",
                                knowledge_search_result=knowledge_search_result,
                                json_search_result=json_search_result, agent_search_result=agent_search_response,
                                suggested_question=[])
        LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                          profile_name=selected_profile, sql="", query=search_box,
                                          intent="reject_search", log_info="", time_str=current_time,
                                          log_type="superset")
        return answer
    # 建议问题
    if gen_suggested_question_flag and (search_intent_flag or agent_intent_flag):
        generated_sq = generate_suggested_question(prompt_map, search_box, model_id=model_type)
        split_strings = generated_sq.split("[generate]")
        generate_suggested_question_list = [s.strip() for s in split_strings if s.strip()]
    if search_intent_flag:
        if normal_search_result.json == "":
            json_search_result.json = "-1"
        else:
            json_search_result.json = normal_search_result.json
            json_search_result.think_process = normal_search_result.process_think
        LogManagement.add_log_to_database(log_id=log_id, user_id=user_id, session_id=session_id,
                                          profile_name=selected_profile, sql=json_search_result.json,
                                          query=search_box,
                                          intent="normal_search",
                                          log_info=json.dumps({
                                              "entity_slot_retrieve": normal_search_result.entity_slot_retrieve,
                                              "retrieve_result": normal_search_result.retrieve_result,
                                              "process_think": normal_search_result.process_think,
                                              "response": normal_search_result.response,
                                          }, ensure_ascii=False),
                                          time_str=current_time, log_type="superset")
        answer = SupersetAnswer(query=search_box, query_intent="normal_search",
                                knowledge_search_result=knowledge_search_result,
                                json_search_result=json_search_result,
                                agent_search_result=agent_search_response,
                                suggested_question=generate_suggested_question_list)
        return answer
