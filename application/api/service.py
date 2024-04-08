import json
import os
from dotenv import load_dotenv
from loguru import logger

from nlq.business.connection import ConnectionManagement
from nlq.business.nlq_chain import NLQChain
from nlq.business.profile import ProfileManagement
from utils.database import get_db_url_dialect
from utils.llm import claude3_to_sql, create_vector_embedding_with_bedrock, \
    retrieve_results_from_opensearch, get_query_intent
from .schemas import Question, Answer, Example
from .exception_handler import BizException
from .constant import const
from .enum import ErrorEnum


load_dotenv()
# load config.json as dictionary
with open(os.path.join(os.getcwd(), 'config_files', '1_config.json')) as f:
    env_vars = json.load(f)
opensearch_config = env_vars['data_sources']['shopping_guide']['opensearch']
for key in opensearch_config:
    opensearch_config[key] = os.getenv(opensearch_config[key].replace('$', ''))
datasource_profile = {}
for i, v in env_vars['data_sources'].items():
    datasource_profile[i] = v
all_profiles = ProfileManagement.get_all_profiles_with_info()
all_profiles.update(datasource_profile)


def verify_parameters(question: Question):
    if question.bedrock_model_id not in const.BEDROCK_MODEL_IDS:
        raise BizException(ErrorEnum.INVAILD_BEDROCK_MODEL_ID)


def ask(question: Question) -> Answer:
    logger.debug(question)
    verify_parameters(question)

    current_nlq_chain = NLQChain(question.profile_name)

    search_intent_flag = True
    current_nlq_chain.set_question(question.keywords)
    retrieve_result = []
    if not current_nlq_chain.get_retrieve_samples():
        if question.use_rag:
            logger.info(f'try to get retrieve samples from open search')
            logger.info('Retrieving samples...')
            try:
                # HACK: always use first opensearch
                selected_profile = "shopping_guide"

                logger.info(question.keywords)
                records_with_embedding = create_vector_embedding_with_bedrock(
                    question.keywords,
                    index_name=env_vars['data_sources'][selected_profile]['opensearch']['index_name'])
                logger.info(env_vars['data_sources'][selected_profile]['opensearch']['index_name'])
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
                    profile_name=selected_profile)
                current_nlq_chain.set_retrieve_samples(retrieve_result)
            except Exception as e:
                logger.exception(e)
                logger.info(f"Failed to retrieve Q/A from OpenSearch: {str(e)}")
                retrieve_result = []
                selected_profile = question.profile_name
    else:
        logger.info(f'get retrieve samples from memory: {len(current_nlq_chain.get_retrieve_samples())}')

    examples = []
    for example in current_nlq_chain.get_retrieve_samples():
        examples.append(Example(
                            score=example['_score'],
                            question=example['_source']['text'],
                            answer=example['_source']['sql'].strip()
                            )
        )

    if not current_nlq_chain.get_generated_sql_response():
        logger.info('try to get generated sql from LLM')
        # Whether Retrieving Few Shots from Database
        logger.info('Sending request...')
        database_profile = all_profiles[selected_profile]
        # fix db url is Empty
        if database_profile['db_url'] == '':
            conn_name = database_profile['conn_name']
            db_url = ConnectionManagement.get_db_url_by_name(conn_name)
            database_profile['db_url'] = db_url

        intent_response = get_query_intent(question.bedrock_model_id, question.keywords)

        intent = intent_response.get("intent", "normal_search")
        if intent == "reject_search":
            search_intent_flag = False

        if search_intent_flag:
            response = claude3_to_sql(database_profile['tables_info'],
                                        database_profile['hints'],
                                        question.keywords,
                                        model_id=question.bedrock_model_id,
                                        examples=retrieve_result,
                                        dialect=get_db_url_dialect(database_profile['db_url']),
                                        model_provider=None)
            logger.info(f'got llm response: {response}')
            current_nlq_chain.set_generated_sql_response(response)
    else:
        logger.info('get generated sql from memory')

    if not search_intent_flag:
        raise BizException(ErrorEnum.NOT_SUPPORTED)

    final_sql_query_result = None
    if question.query_result and search_intent_flag:
        if current_nlq_chain.get_executed_result_df(all_profiles[question.profile_name],force_execute_query=False) is None:
            logger.info('try to execute the generated sql')
            sql_query_result = current_nlq_chain.get_executed_result_df(all_profiles[question.profile_name],)
        if sql_query_result is not None:
            # Reset change flag to False
            current_nlq_chain.set_visualization_config_change(False)
            # final_sql_query_result = json.dumps(sql_query_result.to_dict())
            final_sql_query_result = sql_query_result.to_json(orient='records')
    answer = Answer(
        examples=examples,
        sql=current_nlq_chain.get_generated_sql(),
        sql_explain=current_nlq_chain.get_generated_sql_explain(),
        sql_query_result=final_sql_query_result,
    )
    return answer
