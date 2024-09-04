import logging

from nlq.business.connection import ConnectionManagement
from utils.domain import SearchTextSqlResult
from utils.llm import text_to_sql
from utils.opensearch import get_retrieve_opensearch
from utils.tool import get_generated_sql

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def entity_retrieve_search(entity_slot, opensearch_info, selected_profile):
    entity_slot_retrieve = []
    entity_name_set = set()
    try:
        for each_entity in entity_slot:
            entity_retrieve = get_retrieve_opensearch(opensearch_info, each_entity, "ner",
                                                      selected_profile, 1, 0.7)
            if len(entity_retrieve) > 0:
                for each_entity_retrieve in entity_retrieve:
                    if each_entity_retrieve['_source']['entity'] not in entity_name_set:
                        entity_name_set.add(each_entity_retrieve['_source']['entity'])
                        entity_slot_retrieve.append(each_entity_retrieve)
        return entity_slot_retrieve
    except Exception as e:
        logger.error("entity_search is error")
        logger.error(e)
    return entity_slot_retrieve


def qa_retrieve_search(search_box, opensearch_info, selected_profile):
    qa_retrieve = []
    try:
        qa_retrieve = get_retrieve_opensearch(opensearch_info, search_box, "query",
                                                  selected_profile, 3, 0.5)
        return qa_retrieve
    except Exception as e:
        logger.error("qa_retrieve_search is error")
        logger.error(e)
    return qa_retrieve


def normal_text_search(search_box, model_type, database_profile, entity_slot, opensearch_info, selected_profile,
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

        if len(entity_slot) > 0 and use_rag:
            for each_entity in entity_slot:
                entity_retrieve = get_retrieve_opensearch(opensearch_info, each_entity, "ner",
                                                          selected_profile, 1, 0.7)
                if len(entity_retrieve) > 0:
                    entity_slot_retrieve.extend(entity_retrieve)

        if use_rag:
            retrieve_result = get_retrieve_opensearch(opensearch_info, search_box, "query",
                                                      selected_profile, 3, 0.5)

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
        search_result = SearchTextSqlResult(search_query=search_box, entity_slot_retrieve=entity_slot_retrieve,
                                            retrieve_result=retrieve_result, response=response, sql="")
        search_result.entity_slot_retrieve = entity_slot_retrieve
        search_result.retrieve_result = retrieve_result
        search_result.response = response
        search_result.sql = sql
    except Exception as e:
        logger.error(e)
    return search_result


def agent_text_search(search_box, model_type, database_profile, entity_slot, opensearch_info, selected_profile, use_rag,
                      agent_cot_task_result):
    agent_search_results = []
    default_agent_search_results = []
    default_each_res_dict = {}
    default_each_res_dict["query"] = search_box
    default_each_res_dict["response"] = ""
    default_each_res_dict["sql"] = "-1"
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
            each_task_response = text_to_sql(database_profile['tables_info'],
                                             database_profile['hints'],
                                             database_profile['prompt_map'],
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
        return agent_search_results
    except Exception as e:
        logger.error(e)
    return default_agent_search_results
