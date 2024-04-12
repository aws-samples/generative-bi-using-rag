import requests
import json
import boto3
import boto3
from botocore.config import Config
from opensearchpy import OpenSearch
from utils import opensearch
from utils.prompt import POSTGRES_DIALECT_PROMPT_CLAUDE3, MYSQL_DIALECT_PROMPT_CLAUDE3, \
    DEFAULT_DIALECT_PROMPT, SEARCH_INTENT_PROMPT_CLAUDE3
import os
from loguru import logger
from langchain_core.output_parsers import JsonOutputParser
from utils.prompts.generate_prompt import generate_llm_prompt

BEDROCK_AWS_REGION = os.environ.get('BEDROCK_REGION', 'us-west-2')

config = Config(
    region_name=BEDROCK_AWS_REGION,
    signature_version='v4',
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    }
)
# model IDs are here:
# https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html

bedrock = None
json_parse = JsonOutputParser()


@logger.catch
def get_bedrock_client():
    global bedrock
    if not bedrock:
        bedrock = boto3.client(service_name='bedrock-runtime', config=config)
    return bedrock


def invoke_model_claude3(model_id, system_prompt, messages, max_tokens, with_response_stream=False):
    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": messages,
            "temperature": 0.01
        }
    )

    if with_response_stream:
        response = get_bedrock_client().invoke_model_with_response_stream(body=body, modelId=model_id)
        return response
    else:
        response = get_bedrock_client().invoke_model(body=body, modelId=model_id)
        response_body = json.loads(response.get('body').read())
        return response_body


def claude_select_table():
    pass


def generate_prompt(ddl, hints, search_box, sql_examples=None, ner_example=None, model_id=None, dialect='mysql'):
    long_string = ""
    for table_name, table_data in ddl.items():
        ddl_string = table_data["col_a"] if 'col_a' in table_data else table_data["ddl"]
        long_string += "-- {}表：{}\n".format(table_name, table_data["tbl_a"] if 'tbl_a' in table_data else table_data[
            "description"])
        long_string += ddl_string
        long_string += "\n"

    ddl = long_string

    logger.info(f'{dialect=}')
    if dialect == 'postgresql':
        dialect_prompt = POSTGRES_DIALECT_PROMPT_CLAUDE3
    elif dialect == 'mysql':
        dialect_prompt = MYSQL_DIALECT_PROMPT_CLAUDE3
    elif dialect == 'redshift':
        dialect_prompt = '''You are a Amazon Redshift expert. Given an input question, first create a syntactically 
        correct Redshift query to run, then look at the results of the query and return the answer to the input 
        question.'''
    else:
        dialect_prompt = DEFAULT_DIALECT_PROMPT

    example_sql_prompt = ""
    example_ner_prompt = ""
    if sql_examples:
        for item in sql_examples:
            example_sql_prompt += "Q: " + item['_source']['text'] + "\n"
            example_sql_prompt += "A: ```sql\n" + item['_source']['sql'] + "```\n"

    if ner_example:
        for item in sql_examples:
            example_ner_prompt += "ner: " + item['_source']['entity'] + "\n"
            example_ner_prompt += "ner info:" + item['_source']['comment'] + "\n"

    if example_sql_prompt == "" and example_ner_prompt == "":
        claude_prompt = '''Here is DDL of the database you are working on: 
        ```
        {ddl} 
        ```
        Here are some hints: {hints}
        You need to answer the question: "{question}" in SQL. 
        '''.format(ddl=ddl, hints=hints, question=search_box)
    elif example_sql_prompt != "" and example_ner_prompt == "":
        claude_prompt = '''Here is DDL of the database you are working on:
        ```
        {ddl}
        ```
        Here are some hints: {hints}
        Also, here are some examples of generating SQL using natural language: 
        {examples}
        Now, you need to answer the question: "{question}" in SQL. 
        '''.format(ddl=ddl, hints=hints, examples=example_sql_prompt, question=search_box)
    elif example_sql_prompt == "" and example_ner_prompt != "":
        claude_prompt = '''Here is DDL of the database you are working on:
        ```
        {ddl}
        ```
        Here are some hints: {hints}
        Also, here are some ner info: 
        {examples}
        Now, you need to answer the question: "{question}" in SQL. 
        '''.format(ddl=ddl, hints=hints, examples=example_ner_prompt, question=search_box)
    else:
        claude_prompt = '''Here is DDL of the database you are working on:
        ```
        {ddl}
        ```
        Here are some hints: {hints}
        Here here are some ner info: {examples_ner}
        Also, here are some examples of generating SQL using natural language: 
        {examples_sql}
        Now, you need to answer the question: "{question}" in SQL. 
        '''.format(ddl=ddl, hints=hints, examples_sql=example_sql_prompt, examples_ner=example_ner_prompt,
                   question=search_box)

    return claude_prompt, dialect_prompt


@logger.catch
def claude3_to_sql(ddl, hints, search_box, sql_examples=None, ner_example=None, model_id=None, dialect='mysql',
                   model_provider=None, with_response_stream=False):
    user_prompt, system_prompt = generate_llm_prompt(ddl, hints, search_box, sql_examples, ner_example, model_id,
                                                 dialect=dialect)

    max_tokens = 2048

    # Prompt with user turn only.
    user_message = {"role": "user", "content": user_prompt}
    messages = [user_message]
    logger.info(f'{system_prompt=}')
    logger.info(f'{messages=}')
    response = invoke_model_claude3(model_id, system_prompt, messages, max_tokens, with_response_stream)
    if with_response_stream:
        return response
    else:
        final_response = response.get("content")[0].get("text")
        return final_response


def get_query_intent(model_id, search_box):
    default_intent = {"intent": "normal_search"}
    try:
        system_prompt = SEARCH_INTENT_PROMPT_CLAUDE3
        max_tokens = 2048
        user_message = {"role": "user", "content": search_box}
        messages = [user_message]
        response = invoke_model_claude3(model_id, system_prompt, messages, max_tokens)
        final_response = response.get("content")[0].get("text")
        logger.info(f'{final_response=}')
        intent_result_dict = json_parse.parse(final_response)
        return intent_result_dict
    except Exception as e:
        return default_intent


def create_vector_embedding_with_bedrock(text, index_name):
    payload = {"inputText": f"{text}"}
    body = json.dumps(payload)
    modelId = "amazon.titan-embed-text-v1"
    accept = "application/json"
    contentType = "application/json"

    response = get_bedrock_client().invoke_model(
        body=body, modelId=modelId, accept=accept, contentType=contentType
    )
    response_body = json.loads(response.get("body").read())

    embedding = response_body.get("embedding")
    return {"_index": index_name, "text": text, "vector_field": embedding}


def retrieve_results_from_opensearch(index_name, region_name, domain, opensearch_user, opensearch_password,
                                     query_embedding, top_k=3, host='', port=443, profile_name=None):
    auth = (opensearch_user, opensearch_password)
    if len(host) == 0:
        host = opensearch.get_opensearch_endpoint(domain, region_name)
        port = 443

    # Create the client with SSL/TLS enabled, but hostname verification disabled.
    opensearch_client = OpenSearch(
        hosts=[{'host': host, 'port': port}],
        http_compress=True,  # enables gzip compression for request bodies
        http_auth=auth,
        use_ssl=True,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False
    )
    search_query = {
        "size": top_k,  # Adjust the size as needed to retrieve more or fewer results
        "query": {
            "bool": {
                "filter": {
                    "match_phrase": {
                        "profile": profile_name
                    }
                },
                "must": [
                    {
                        "knn": {
                            "vector_field": {  # Make sure 'vector_field' is the name of your vector field in OpenSearch
                                "vector": query_embedding,
                                "k": top_k  # Adjust k as needed to retrieve more or fewer nearest neighbors
                            }
                        }
                    }
                ]
            }

        }
    }

    # Execute the search query
    response = opensearch_client.search(
        body=search_query,
        index=index_name
    )

    return response['hits']['hits']


def upload_results_to_opensearch(region_name, domain, opensearch_user, opensearch_password, index_name, query, sql,
                                 host='', port=443):
    auth = (opensearch_user, opensearch_password)
    if len(host) == 0:
        host = opensearch.get_opensearch_endpoint(domain, region_name)
        port = 443
    # Create the client with SSL/TLS enabled, but hostname verification disabled.
    opensearch_client = OpenSearch(
        hosts=[{'host': host, 'port': port}],
        http_compress=True,  # enables gzip compression for request bodies
        http_auth=auth,
        use_ssl=True,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False
    )

    # Vector embedding using Amazon Bedrock Titan text embedding
    logger.info(f"Creating embeddings for records")
    record_with_embedding = create_vector_embedding_with_bedrock(query, index_name)

    record_with_embedding['sql'] = sql
    success, failed = opensearch.put_bulk_in_opensearch([record_with_embedding], opensearch_client)
    if success == 1:
        logger.info("Finished creating records using Amazon Bedrock Titan text embedding")
        return True
    else:
        logger.error("Failed to create records using Amazon Bedrock Titan text embedding")
        return False


def generate_suggested_question(search_box, system_prompt, model_id=None):
    max_tokens = 2048
    user_prompt = """
    Here is the input query: {question}. 
    Please generate queries based on the input query.
    """.format(question=search_box)
    user_message = {"role": "user", "content": user_prompt}
    messages = [user_message]
    logger.info(f'{system_prompt=}')
    logger.info(f'{messages=}')
    response = invoke_model_claude3(model_id, system_prompt, messages, max_tokens)
    final_response = response.get("content")[0].get("text")

    return final_response
