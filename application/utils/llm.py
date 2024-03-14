import requests
import json
import boto3
import boto3
from botocore.config import Config
from opensearchpy import OpenSearch
from utils import opensearch
import os
from loguru import logger

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


@logger.catch
def get_bedrock_client():
    global bedrock
    if not bedrock:
        bedrock = boto3.client(service_name='bedrock-runtime', config=config)
    return bedrock


def sqlcoder(SQLCODER_API_ENDPOINT, payload):
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(SQLCODER_API_ENDPOINT, headers=headers, data=json.dumps(payload))
    return response


def invoke_model(payload, model_id):
    body = json.dumps(payload)

    accept = 'application/json'
    contentType = 'application/json'

    response = get_bedrock_client().invoke_model(body=body, modelId=model_id, accept=accept, contentType=contentType)
    response_body = json.loads(response.get('body').read())
    # logger.info(f'{response_body=}')
    if 'anthropic.claude' in model_id:
        result_key = 'completion'
    elif 'meta.llama2' in model_id:
        result_key = 'generation'
    return response_body[result_key]


def claude_select_table():
    pass


DEFAULT_DIALECT_PROMPT = '''You are a data analyst who writes SQL statements.'''

TOP_K = 100
POSTGRES_DIALECT_PROMPT = """You are a PostgreSQL expert. Given an input question, first create a syntactically correct PostgreSQL query to run, then look at the results of the query and return the answer to the input question.
Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per PostgreSQL. You can order the results to return the most informative data in the database.
Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.
Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
Pay attention to use CURRENT_DATE function to get the current date, if the question involves "today".""".format(top_k=TOP_K)

MYSQL_DIALECT_PROMPT = """You are a MySQL expert. Given an input question, create a syntactically correct MySQL query to run.
Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per MySQL. You can order the results to return the most informative data in the database.
Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in backticks (`) to denote them as delimited identifiers.
Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
Pay attention to use CURDATE() function to get the current date, if the question involves "today".""".format(top_k=TOP_K)

def claude_to_sql(ddl, hints, search_box, examples=None, model_id='anthropic.claude-v2:1', dialect='mysql', model_provider=None):
    long_string = ""
    for table_name, table_data in ddl.items():

        ddl_string = table_data["col_a"] if 'col_a' in table_data else table_data["ddl"]
        long_string += "-- {}表：{}\n".format(table_name, table_data["tbl_a"] if 'tbl_a' in table_data else table_data["description"])
        long_string += ddl_string
        long_string += "\n"

    ddl = long_string

    logger.info(f'{dialect=}')
    if dialect == 'postgresql':
        dialect_prompt = POSTGRES_DIALECT_PROMPT
    elif dialect == 'mysql':
        dialect_prompt = MYSQL_DIALECT_PROMPT
    elif dialect == 'redshift':
        dialect_prompt = '''You are a Amazon Redshift expert. Given an input question, first create a syntactically correct Redshift query to run, then look at the results of the query and return the answer to the input question.'''
    else:
        dialect_prompt = DEFAULT_DIALECT_PROMPT

    example_prompt = ""
    if not examples:
        prompt = '''Human:
{dialect_prompt}
Here is DDL of the database you are working on:
```sql
{ddl}
```
Please do not perform any modifications to SQL tables.
Absolutely do not output any columns, tables, or other information that is not mentioned in the database. Ensure that the program runs without errors.
Here are some hints:
{hints}
You need to answer the question: "{question}" in SQL. Please give the SQL statement that can answer the question. Aside from giving the SQL answer, concisely explain yourself after giving the answer in same language as the question.
Assistant:'''.format(dialect_prompt=dialect_prompt, ddl=ddl, hints=hints, question=search_box)
        logger.info(f'{prompt=}')
        claude_prompt = prompt
    else:
        # assemble examples into a string
        for item in examples:
            example_prompt += "Q: " + item['_source']['text'] + "\n"
            example_prompt += "A: ```sql\n" + item['_source']['sql'] + "```\n"

        claude_prompt = '''Human:
{dialect_prompt}
Here is DDL of the database you are working on:
```sql
{ddl}
```
Please do not perform any modifications to SQL tables.
Absolutely do not output any columns, tables, or other information that is not mentioned in the database. Ensure that the program runs without errors.
Here are some hints:
{hints}
DO NOT use window function in another function's argument.
Also, here are some examples of generating SQL using natural language:
{examples}
Now, you need to answer the question: "{question}" in SQL. Please give the SQL statement that can answer the question. Aside from giving the SQL answer, concisely explain yourself after giving the answer in same language as the question.
Assistant:'''.format(dialect_prompt=dialect_prompt, ddl=ddl, hints=hints, examples=example_prompt, question=search_box)

        llama_prompt = '''[INST]{dialect_prompt}[/INST]
Here is DDL of the database you are working on:
```sql
{ddl}
```
Please do not perform any modifications to SQL tables.
Absolutely do not output any columns, tables, or other information that is not mentioned in the database. Ensure that the program runs without errors.
Here are some hints:
{hints}
Also, here are some examples of generating SQL using natural language:
{examples}
Now, you need to answer the question: "{question}" in SQL. 
Please give the SQL statement that can answer the question. 
SQL Query:'''.format(dialect_prompt=dialect_prompt, ddl=ddl, hints=hints, examples=example_prompt, question=search_box)

    if model_provider == 'replicate':
        response = None
        # from utils.opensource_llm import invoke_model_replicate
        # response = invoke_model_replicate(model_id, ddl, hints, dialect_prompt, example_prompt, search_box)
    else:
        payload = {
            # "prompt": prompt,
            # "max_tokens_to_sample": 1024,
            "temperature": 0.01,
            "top_p": 0.9,
        }
        if 'anthropic.claude' in model_id:
            payload['max_tokens_to_sample'] = 1024
            payload['prompt'] = claude_prompt
        elif 'meta.llama2' in model_id:
            payload['max_gen_len'] = 1024
            payload['prompt'] = llama_prompt
        logger.info(f"{payload['prompt']=}")
        print(payload['prompt'])
        response = invoke_model(payload, model_id=model_id)
    return response


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
