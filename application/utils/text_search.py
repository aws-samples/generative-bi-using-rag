from api.enum import ContentEnum
from utils.llm import text_to_sql
from utils.logging import getLogger
from utils.opensearch import get_retrieve_opensearch
from utils.tool import get_generated_sql

import json
from fastapi import  WebSocket
from utils.tool import serialize_timestamp

logger = getLogger()


def entity_retrieve_search(entity_slot, opensearch_info, selected_profile):
    entity_slot_retrieve = []
    entity_name_set = set()
    for each_entity in entity_slot:
        entity_retrieve = get_retrieve_opensearch(opensearch_info, each_entity, "ner",
                                                  selected_profile, 1, 0.7)
        if len(entity_retrieve) > 0:
            for each_entity_retrieve in entity_retrieve:
                if each_entity_retrieve['_source']['entity'] not in entity_name_set:
                    entity_name_set.add(each_entity_retrieve['_source']['entity'])
                    entity_slot_retrieve.append(each_entity_retrieve)
    return entity_slot_retrieve


def qa_retrieve_search(search_box, opensearch_info, selected_profile):
    qa_retrieve = []
    qa_retrieve = get_retrieve_opensearch(opensearch_info, search_box, "query",
                                          selected_profile, 3, 0.5)
    return qa_retrieve

def agent_text_search(search_box, model_type, database_profile, entity_slot, opensearch_info, selected_profile, use_rag,
                      agent_cot_task_result):
    agent_search_results = []
    default_agent_search_results = []
    default_each_res_dict = {}
    default_each_res_dict["query"] = search_box
    default_each_res_dict["response"] = ""
    default_each_res_dict["sql"] = "-1"
    token_info = {}
    token_info["input_tokens"] = 0
    token_info["output_tokens"] = 0
    try:
        for each_task in agent_cot_task_result:
            each_res_dict = {}
            each_task_query = agent_cot_task_result[each_task]
            each_res_dict["query"] = each_task_query
            entity_slot_retrieve = []
            retrieve_result = []
            if use_rag:
                entity_slot_retrieve = get_retrieve_opensearch(opensearch_info, each_task_query, "ner",
                                                               selected_profile, 3, 0.5)

                retrieve_result = get_retrieve_opensearch(opensearch_info, each_task_query, "query",
                                                          selected_profile, 3, 0.5)
            each_task_response, model_response = text_to_sql(database_profile['tables_info'],
                                                             database_profile['hints'],
                                                             database_profile['prompt_map'],
                                                             each_task_query,
                                                             model_id=model_type,
                                                             sql_examples=retrieve_result,
                                                             ner_example=entity_slot_retrieve,
                                                             dialect=database_profile['db_type'],
                                                             model_provider=None)
            if model_response.token_info is not None and len(model_response.token_info) > 0:
                sub_token_info = model_response.token_info
                if "input_tokens" in sub_token_info:
                    token_info["input_tokens"] = token_info["input_tokens"] + sub_token_info["input_tokens"]
                if "output_tokens" in sub_token_info:
                    token_info["output_tokens"] = token_info["output_tokens"] + sub_token_info["output_tokens"]
            each_task_sql = get_generated_sql(each_task_response)
            each_res_dict["response"] = each_task_response
            each_res_dict["sql"] = each_task_sql
            if each_res_dict["sql"] != "":
                agent_search_results.append(each_res_dict)
        return agent_search_results, token_info
    except Exception as e:
        logger.error(e)
    return default_agent_search_results, token_info


async def agent_text_search_websocket(websocket, session_id, user_id, search_box, model_type, database_profile,
                                      entity_slot, opensearch_info, selected_profile, use_rag,
                                      agent_cot_task_result):
    agent_search_results = []
    default_agent_search_results = []
    default_each_res_dict = {}
    default_each_res_dict["query"] = search_box
    default_each_res_dict["response"] = ""
    default_each_res_dict["sql"] = "-1"
    token_info = {}
    token_info["input_tokens"] = 0
    token_info["output_tokens"] = 0
    index = 1
    try:
        for each_task in agent_cot_task_result:
            await response_websocket(websocket, session_id, "Agent SQL Task_{index} Generating".format(index=str(index)),
                                     ContentEnum.STATE,"start", user_id)
            each_res_dict = {}
            each_task_query = agent_cot_task_result[each_task]
            each_res_dict["query"] = each_task_query
            entity_slot_retrieve = []
            retrieve_result = []
            if use_rag:
                entity_slot_retrieve = get_retrieve_opensearch(opensearch_info, each_task_query, "ner",
                                                               selected_profile, 3, 0.5)

                retrieve_result = get_retrieve_opensearch(opensearch_info, each_task_query, "query",
                                                          selected_profile, 3, 0.5)
            each_task_response, model_response = text_to_sql(database_profile['tables_info'],
                                                             database_profile['hints'],
                                                             database_profile['prompt_map'],
                                                             each_task_query,
                                                             model_id=model_type,
                                                             sql_examples=retrieve_result,
                                                             ner_example=entity_slot_retrieve,
                                                             dialect=database_profile['db_type'],
                                                             model_provider=None)
            await response_websocket(websocket, session_id, "Agent SQL Task_{index} Generating".format(index=str(index)),  ContentEnum.STATE,
                                     "end", user_id)
            index = index + 1
            if model_response.token_info is not None and len(model_response.token_info) > 0:
                sub_token_info = model_response.token_info
                if "input_tokens" in sub_token_info:
                    token_info["input_tokens"] = token_info["input_tokens"] + sub_token_info["input_tokens"]
                if "output_tokens" in sub_token_info:
                    token_info["output_tokens"] = token_info["output_tokens"] + sub_token_info["output_tokens"]
            each_task_sql = get_generated_sql(each_task_response)
            each_res_dict["response"] = each_task_response
            each_res_dict["sql"] = each_task_sql
            if each_res_dict["sql"] != "":
                agent_search_results.append(each_res_dict)
        return agent_search_results, token_info
    except Exception as e:
        logger.error(e)
    return default_agent_search_results, token_info


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