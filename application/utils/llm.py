import json
import boto3
from botocore.config import Config

from utils.prompt import POSTGRES_DIALECT_PROMPT_CLAUDE3, MYSQL_DIALECT_PROMPT_CLAUDE3, \
    DEFAULT_DIALECT_PROMPT, SEARCH_INTENT_PROMPT_CLAUDE3, AWS_REDSHIFT_DIALECT_PROMPT_CLAUDE3
import os
import logging
from langchain_core.output_parsers import JsonOutputParser
from utils.prompts.generate_prompt import generate_llm_prompt, generate_agent_cot_system_prompt, \
    generate_intent_prompt, generate_knowledge_prompt, generate_data_visualization_prompt, \
    generate_agent_analyse_prompt, generate_data_summary_prompt, generate_suggest_question_prompt, \
    generate_query_rewrite_prompt

from utils.env_var import bedrock_ak_sk_info, BEDROCK_REGION, BEDROCK_EMBEDDING_MODEL, SAGEMAKER_EMBEDDING_REGION, \
    SAGEMAKER_SQL_REGION
from utils.tool import convert_timestamps_to_str

from nlq.business.model import ModelManagement

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

config = Config(
    region_name=BEDROCK_REGION,
    signature_version='v4',
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    },
    read_timeout=600
)
# model IDs are here:
# https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html

bedrock = None
json_parse = JsonOutputParser()
embedding_sagemaker_client = None
sagemaker_client = None


def get_bedrock_client():
    global bedrock
    if not bedrock:
        if len(bedrock_ak_sk_info) == 0:
            bedrock = boto3.client(service_name='bedrock-runtime', config=config)
        else:
            bedrock = boto3.client(
                service_name='bedrock-runtime', config=config,
                aws_access_key_id=bedrock_ak_sk_info['access_key_id'],
                aws_secret_access_key=bedrock_ak_sk_info['secret_access_key'])
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


def invoke_llama_70b(model_id, system_prompt, user_prompt, max_tokens, with_response_stream=False):
    """
    Invoke LLama-70B model
    :param model_id:
    :param system_prompt:
    :param messages:
    :param max_tokens:
    :param with_response_stream:
    :return:
    """
    try:
        llama3_prompt = """
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>

        {system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>

        {user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
        """
        body = {
            "prompt": llama3_prompt.format(system_prompt=system_prompt, user_prompt=user_prompt),
            "max_gen_len": 2048,
            "temperature": 0.01,
            "top_p": 0.9
        }
        if with_response_stream:
            response = get_bedrock_client().invoke_model_with_response_stream(body=json.dumps(body), modelId=model_id)
            return response
        else:
            response = get_bedrock_client().invoke_model(
                modelId=model_id, body=json.dumps(body)
            )
            response_body = json.loads(response["body"].read())
            return response_body
    except Exception as e:
        logger.error("Couldn't invoke LLama 70B")
        logger.error(e)


def invoke_mixtral_8x7b(model_id, system_prompt, messages, max_tokens, with_response_stream=False):
    """
    Invokes the Mixtral 8c7B model to run an inference using the input
    provided in the request body.

    :param prompt: The prompt that you want Mixtral to complete.
    :return: List of inference responses from the model.
    """

    try:
        instruction = f"<s>[INST] {system_prompt} \n The question you need to answer is: <question> {messages[0]['content']} </question>[/INST]"
        body = {
            "prompt": instruction,
            # "system": system_prompt,
            # "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.01,
        }

        if with_response_stream:
            response = get_bedrock_client().invoke_model_with_response_stream(body=json.dumps(body), modelId=model_id)
            return response
        else:
            response = get_bedrock_client().invoke_model(
                modelId=model_id, body=json.dumps(body)
            )
            response_body = json.loads(response["body"].read())
            response_body['content'] = response_body['outputs']
            return response_body
    except Exception as e:
        logger.error("Couldn't invoke Mixtral 8x7B")
        logger.error(e)
        raise


def get_embedding_sagemaker_client():
    global embedding_sagemaker_client
    if not embedding_sagemaker_client:
        if SAGEMAKER_EMBEDDING_REGION is not None and SAGEMAKER_EMBEDDING_REGION != "":
            embedding_sagemaker_client = boto3.client(service_name='sagemaker-runtime',
                                                      region_name=SAGEMAKER_EMBEDDING_REGION)
        else:
            embedding_sagemaker_client = boto3.client(service_name='sagemaker-runtime')
    return embedding_sagemaker_client


def get_sagemaker_client():
    global sagemaker_client
    if not sagemaker_client:
        if SAGEMAKER_SQL_REGION is not None and SAGEMAKER_SQL_REGION != "":
            sagemaker_client = boto3.client(service_name='sagemaker-runtime',
                                            region_name=SAGEMAKER_SQL_REGION)
        else:
            sagemaker_client = boto3.client(service_name='sagemaker-runtime')
    return sagemaker_client

def invoke_model_sagemaker_endpoint(endpoint_name, body, model_type="LLM", with_response_stream=False):
    if with_response_stream:
        if model_type == "LLM":
            response = get_sagemaker_client().invoke_endpoint_with_response_stream(
                EndpointName=endpoint_name,
                Body=body,
                ContentType="application/json",
            )
            return response
        else:
            response = get_embedding_sagemaker_client().invoke_endpoint_with_response_stream(
                EndpointName=endpoint_name,
                Body=body,
                ContentType="application/json",
            )
        return response
    else:
        if model_type == "LLM":
            response = get_sagemaker_client().invoke_endpoint(
                EndpointName=endpoint_name,
                Body=body,
                ContentType="application/json",
            )
            response_body = json.loads(response.get('Body').read())
            return response_body
        else:
            response = get_embedding_sagemaker_client().invoke_endpoint(
                EndpointName=endpoint_name,
                Body=body,
                ContentType="application/json",
            )
            response_body = json.loads(response.get('Body').read())
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
        dialect_prompt = AWS_REDSHIFT_DIALECT_PROMPT_CLAUDE3
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
    print('claude_prompt')

    return claude_prompt, dialect_prompt


def invoke_llm_model(model_id, system_prompt, user_prompt, max_tokens=2048, with_response_stream=False):
    # Prompt with user turn only.
    user_message = {"role": "user", "content": user_prompt}
    messages = [user_message]
    logger.info(f'{system_prompt=}')
    logger.info(f'{messages=}')
    response = ""
    model_config = {}
    try:
        if model_id.startswith('anthropic.claude-3'):
            response = invoke_model_claude3(model_id, system_prompt, messages, max_tokens, with_response_stream)
        elif model_id.startswith('mistral.mixtral-8x7b'):
            response = invoke_mixtral_8x7b(model_id, system_prompt, messages, max_tokens, with_response_stream)
        elif model_id.startswith('meta.llama3-70b'):
            response = invoke_llama_70b(model_id, system_prompt, user_prompt, max_tokens, with_response_stream)
        elif model_id.startswith('sagemaker.'):
            model_config = ModelManagement.get_model_by_id(model_id)
            prompt_template = model_config['prompt_template']
            input_payload = model_config['input_payload']
            prompt = prompt_template.replace("SYSTEM_PROMPT", system_prompt).replace("USER_PROMPT", user_prompt)
            input_payload = input_payload.replace("INPUT", prompt)
            logger.info(f'{input_payload=}')
            body = json.loads(input_payload)
            endpoint_name = model_id[len('sagemaker.'):]
            response = invoke_model_sagemaker_endpoint(endpoint_name, body, "LLM", with_response_stream)
        if with_response_stream:
            return response
        else:
            if model_id.startswith('meta.llama3-70b'):
                return response["generation"]
            elif model_id.startswith('sagemaker.'):
                output_format = model_config['output_format']
                response = eval(output_format)
                return response
            else:
                final_response = response.get("content")[0].get("text")
                return final_response
    except Exception as e:
        logger.error("invoke_llm_model error {}".format(e))
    return response


def text_to_sql(ddl, hints, prompt_map, search_box, sql_examples=None, ner_example=None, model_id=None, dialect='mysql',
                model_provider=None, with_response_stream=False, additional_info=''):
    user_prompt, system_prompt = generate_llm_prompt(ddl, hints, prompt_map, search_box, sql_examples, ner_example,
                                                     model_id, dialect=dialect)
    max_tokens = 4096
    response = invoke_llm_model(model_id, system_prompt, user_prompt + additional_info, max_tokens, with_response_stream)
    return response


def get_agent_cot_task(model_id, prompt_map, search_box, ddl, agent_cot_example=None):
    default_agent_cot_task = {"task_1": search_box}
    user_prompt, system_prompt = generate_agent_cot_system_prompt(ddl, prompt_map, search_box, model_id,
                                                                  agent_cot_example)
    try:
        max_tokens = 2048
        final_response = invoke_llm_model(model_id, system_prompt, user_prompt, max_tokens, False)
        logger.info(f'{final_response=}')
        intent_result_dict = json_parse.parse(final_response)
        return intent_result_dict
    except Exception as e:
        logger.error("get_agent_cot_task is error:{}".format(e))
        return default_agent_cot_task


def data_analyse_tool(model_id, prompt_map, search_box, sql_data, search_type):
    try:
        max_tokens = 2048
        if search_type == "agent":
            user_prompt, system_prompt = generate_agent_analyse_prompt(prompt_map, search_box, model_id, sql_data)
        else:
            user_prompt, system_prompt = generate_data_summary_prompt(prompt_map, search_box, model_id, sql_data)
        final_response = invoke_llm_model(model_id, system_prompt, user_prompt, max_tokens, False)
        logger.info(f'{final_response=}')
        return final_response
    except Exception as e:
        logger.error("data_analyse_tool is error")
    return ""


def get_query_intent(model_id, search_box, prompt_map):
    default_intent = {"intent": "normal_search"}
    try:
        user_prompt, system_prompt = generate_intent_prompt(prompt_map, search_box, model_id)
        max_tokens = 2048
        final_response = invoke_llm_model(model_id, system_prompt, user_prompt, max_tokens, False)
        logger.info(f'{final_response=}')
        intent_result_dict = json_parse.parse(final_response)
        return intent_result_dict
    except Exception as e:
        logger.error("get_query_intent is error:{}".format(e))
        return default_intent


def get_query_rewrite(model_id, search_box, prompt_map, chat_history):
    query_rewrite = {"intent": "original_problem", "query": search_box}
    history_query = "\n".join(chat_history)
    try:
        user_prompt, system_prompt = generate_query_rewrite_prompt(prompt_map, search_box, model_id, history_query)
        max_tokens = 2048
        final_response = invoke_llm_model(model_id, system_prompt, user_prompt, max_tokens, False)
        query_rewrite_result = json_parse.parse(final_response)
        logger.info(f'{final_response=}')
        return query_rewrite_result
    except Exception as e:
        logger.error("get_query_rewrite is error:{}".format(e))
        return query_rewrite


def knowledge_search(model_id, search_box, prompt_map):
    try:
        user_prompt, system_prompt = generate_knowledge_prompt(prompt_map, search_box, model_id)
        max_tokens = 2048
        final_response = invoke_llm_model(model_id, system_prompt, user_prompt, max_tokens, False)
        return final_response
    except Exception as e:
        logger.error("knowledge_search is error")
    return ""


def select_data_visualization_type(model_id, search_box, search_data, prompt_map):
    default_data_visualization = {
        "show_type": "table",
        "format_data": []
    }
    try:
        user_prompt, system_prompt = generate_data_visualization_prompt(prompt_map, search_box, search_data, model_id)
        max_tokens = 2048
        final_response = invoke_llm_model(model_id, system_prompt, user_prompt, max_tokens, False)
        data_visualization_dict = json_parse.parse(final_response)
        return data_visualization_dict
    except Exception as e:
        logger.error("select_data_visualization_type is error {}", e)
        return default_data_visualization


def data_visualization(model_id, search_box, search_data, prompt_map):
    search_data = search_data.fillna("")
    columns = list(search_data.columns)
    data_list = search_data.values.tolist()
    all_columns_data = [columns] + data_list
    all_columns_data = convert_timestamps_to_str(all_columns_data)
    try:
        if len(all_columns_data) < 1:
            return "table", all_columns_data, "-1", []
        else:
            if len(all_columns_data) > 10:
                all_columns_data_sample = all_columns_data[0:5]
            else:
                all_columns_data_sample = all_columns_data
            model_select_type_dict = select_data_visualization_type(model_id, search_box, all_columns_data_sample,
                                                                    prompt_map)
            model_select_type = model_select_type_dict["show_type"]
            model_select_type_columns = model_select_type_dict["format_data"][0]
            data_list = search_data[model_select_type_columns].values.tolist()

            # 返回格式校验
            if len(columns) != 2:
                if model_select_type == "table":
                    return "table", all_columns_data, "-1", []
                else:
                    if len(model_select_type_columns) == 2:
                        return "table", all_columns_data, model_select_type, [model_select_type_columns] + data_list
                    else:
                        return "table", all_columns_data, "-1", []
            else:
                if model_select_type == "table":
                    return "table", all_columns_data, "-1", []
                else:
                    return model_select_type, [model_select_type_columns] + data_list, "-1", []
    except Exception as e:
        logger.error("data_visualization is error {}", e)
        return "table", all_columns_data, "-1", []


def create_vector_embedding_with_bedrock(text, index_name):
    payload = {"inputText": f"{text}"}
    body = json.dumps(payload)
    modelId = BEDROCK_EMBEDDING_MODEL
    accept = "application/json"
    contentType = "application/json"

    response = get_bedrock_client().invoke_model(
        body=body, modelId=modelId, accept=accept, contentType=contentType
    )
    response_body = json.loads(response.get("body").read())

    embedding = response_body.get("embedding")
    return {"_index": index_name, "text": text, "vector_field": embedding}


def create_vector_embedding_with_sagemaker(endpoint_name, text, index_name):
    body = json.dumps(
        {
            "inputs": text,
            "is_query": True
        }
    )
    response = invoke_model_sagemaker_endpoint(endpoint_name, body, model_type="embedding")
    embeddings = response[0]
    return {"_index": index_name, "text": text, "vector_field": embeddings}


def generate_suggested_question(prompt_map, search_box, model_id=None):
    max_tokens = 2048
    user_prompt, system_prompt = generate_suggest_question_prompt(prompt_map, search_box, model_id)
    user_message = {"role": "user", "content": user_prompt}
    messages = [user_message]
    logger.info(f'{system_prompt=}')
    logger.info(f'{messages=}')
    response = invoke_model_claude3(model_id, system_prompt, messages, max_tokens)
    final_response = response.get("content")[0].get("text")

    return final_response
