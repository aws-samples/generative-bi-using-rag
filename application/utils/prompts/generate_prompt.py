from utils.prompt import POSTGRES_DIALECT_PROMPT_CLAUDE3, MYSQL_DIALECT_PROMPT_CLAUDE3, \
    DEFAULT_DIALECT_PROMPT
from utils.prompts import guidance_prompt
from utils.prompts import table_prompt
import logging

logger = logging.getLogger(__name__)

support_model_ids_map = {
    "anthropic.claude-3-haiku-20240307-v1:0":"haiku-20240307v1-0",
    "anthropic.claude-3-sonnet-20240229-v1:0":"sonnet-20240229v1-0"
}

system_prompt_dict = {}

system_prompt_dict['haiku-20240307v1-0'] = """
{dialect_prompt}

Assume a database with the following tables and columns exists:

Given the following database schema, transform the following natural language requests into valid SQL queries.

<table_schema>

{sql_schema}

</table_schema>

Here are some examples of generated SQL using natural language.

<examples>

{examples}

</examples> 

Here are some ner info to help generate SQL.

<ner_info>

{ner_info}

</ner_info> 

You ALWAYS follow these guidelines when writing your response:

<guidelines>

{sql_guidance}

</guidelines> 

Think about the sql question before continuing. If it's not about writing SQL statements, say 'Sorry, please ask something relating to querying tables'.

Think about your answer first before you respond. Put your sql in <sql></sql> tags.

"""

system_prompt_dict['sonnet-20240229v1-0'] = """
{dialect_prompt}

Assume a database with the following tables and columns exists:

Given the following database schema, transform the following natural language requests into valid SQL queries.

<table_schema>

{sql_schema}

</table_schema>

Here are some examples of generated SQL using natural language.

<examples>

{examples}

</examples> 

Here are some ner info to help generate SQL.

<ner_info>

{ner_info}

</ner_info> 

You ALWAYS follow these guidelines when writing your response:

<guidelines>

{sql_guidance}

</guidelines> 

Think about the sql question before continuing. If it's not about writing SQL statements, say 'Sorry, please ask something relating to querying tables'.

Think about your answer first before you respond. Put your sql in <sql></sql> tags.

"""

class SystemPromptMapper:
    def __init__(self):
        self.variable_map = system_prompt_dict

    def get_variable(self, name):
        return self.variable_map.get(name)


system_prompt_mapper = SystemPromptMapper()
table_prompt_mapper = table_prompt.TablePromptMapper()
guidance_prompt_mapper = guidance_prompt.GuidancePromptMapper()

def generate_llm_prompt(ddl, hints, search_box, sql_examples=None, ner_example=None, model_id=None, dialect='mysql'):
    long_string = ""
    for table_name, table_data in ddl.items():
        ddl_string = table_data["col_a"] if 'col_a' in table_data else table_data["ddl"]
        long_string += "{}：{}\n".format(table_name, table_data["tbl_a"] if 'tbl_a' in table_data else table_data[
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
        for item in ner_example:
            example_ner_prompt += "ner: " + item['_source']['entity'] + "\n"
            example_ner_prompt += "ner info:" + item['_source']['comment'] + "\n"

    name = support_model_ids_map[model_id]
    system_prompt = system_prompt_mapper.get_variable(name)
    if long_string == '':
        table_prompt = table_prompt_mapper.get_variable(name)
    else:
        table_prompt = long_string
    guidance_prompt = guidance_prompt_mapper.get_variable(name)
    
    system_prompt = system_prompt.format(dialect_prompt=dialect_prompt, sql_schema=table_prompt, sql_guidance=guidance_prompt, examples=example_sql_prompt, ner_info=example_ner_prompt)

    user_prompt = search_box

    return user_prompt, system_prompt


# TODO Must modify prompt
def generate_sagemaker_intent_prompt(
    query: str,
    history=[],
    meta_instruction="You are an AI assistant whose name is InternLM (书生·浦语).\n"
    "- InternLM (书生·浦语) is a conversational language model that is developed by Shanghai AI Laboratory (上海人工智能实验室). It is designed to be helpful, honest, and harmless.\n"
    "- InternLM (书生·浦语) can understand and communicate fluently in the language chosen by the user such as English and 中文.",
):
    prompt = ""
    if meta_instruction:
        prompt += f"""<|im_start|>system\n{meta_instruction}<|im_end|>\n"""
    for record in history:
        prompt += f"""<|im_start|>user\n{record[0]}<|im_end|>\n<|im_start|>assistant\n{record[1]}<|im_end|>\n"""
    prompt += f"""<|im_start|>user\n{query}<|im_end|>\n<|im_start|>assistant\n"""
    return prompt


# TODO Must modify prompt
def generate_sagemaker_sql_prompt(ddl, hints, question, sql_examples=None, ner_example=None, dialect='mysql'):
    prompt = """### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION]

### Instructions
- If you cannot answer the question with the available database schema, return 'I do not know'
- Remember that revenue is price multiplied by quantity
- Remember that cost is supply_price multiplied by quantity

### Database Schema
This query will run on a database whose schema is represented in this string:
CREATE TABLE products (
  product_id INTEGER PRIMARY KEY, -- Unique ID for each product
  name VARCHAR(50), -- Name of the product
  price DECIMAL(10,2), -- Price of each unit of the product
  quantity INTEGER  -- Current quantity in stock
);

CREATE TABLE customers (
   customer_id INTEGER PRIMARY KEY, -- Unique ID for each customer
   name VARCHAR(50), -- Name of the customer
   address VARCHAR(100) -- Mailing address of the customer
);

CREATE TABLE salespeople (
  salesperson_id INTEGER PRIMARY KEY, -- Unique ID for each salesperson
  name VARCHAR(50), -- Name of the salesperson
  region VARCHAR(50) -- Geographic sales region
);

CREATE TABLE sales (
  sale_id INTEGER PRIMARY KEY, -- Unique ID for each sale
  product_id INTEGER, -- ID of product sold
  customer_id INTEGER,  -- ID of customer who made purchase
  salesperson_id INTEGER, -- ID of salesperson who made the sale
  sale_date DATE, -- Date the sale occurred
  quantity INTEGER -- Quantity of product sold
);

CREATE TABLE product_suppliers (
  supplier_id INTEGER PRIMARY KEY, -- Unique ID for each supplier
  product_id INTEGER, -- Product ID supplied
  supply_price DECIMAL(10,2) -- Unit price charged by supplier
);

-- sales.product_id can be joined with products.product_id
-- sales.customer_id can be joined with customers.customer_id
-- sales.salesperson_id can be joined with salespeople.salesperson_id
-- product_suppliers.product_id can be joined with products.product_id

### Answer
Given the database schema, here is the SQL query that answers [QUESTION]{question}[/QUESTION]
[SQL]
"""
    prompt = prompt.format(question=question)
    return prompt


# TODO need to modify prompt
def generate_sagemaker_explain_prompt(
    query: str,
    history=[],
    meta_instruction="You are an AI assistant whose name is InternLM (书生·浦语).\n"
    "- InternLM (书生·浦语) is a conversational language model that is developed by Shanghai AI Laboratory (上海人工智能实验室). It is designed to be helpful, honest, and harmless.\n"
    "- InternLM (书生·浦语) can understand and communicate fluently in the language chosen by the user such as English and 中文.",
):
    prompt = ""
    if meta_instruction:
        prompt += f"""<|im_start|>system\n{meta_instruction}<|im_end|>\n"""
    for record in history:
        prompt += f"""<|im_start|>user\n{record[0]}<|im_end|>\n<|im_start|>assistant\n{record[1]}<|im_end|>\n"""
    prompt += f"""<|im_start|>user\n{query}<|im_end|>\n<|im_start|>assistant\n"""
    return prompt