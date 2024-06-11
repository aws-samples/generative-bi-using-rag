DEFAULT_DIALECT_PROMPT = '''You are a data analyst who writes SQL statements.'''

TOP_K = 100

POSTGRES_DIALECT_PROMPT_CLAUDE3 = """You are a data analysis expert and proficient in PostgreSQL. Given an input question, first create a syntactically correct PostgreSQL query to run.
Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per PostgreSQL. 
Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.
Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
Pay attention to use CURRENT_DATE function to get the current date, if the question involves "today". Aside from giving the SQL answer, concisely explain yourself after giving the answer
in the same language as the question.""".format(top_k=TOP_K)

MYSQL_DIALECT_PROMPT_CLAUDE3 = """You are a data analysis expert and proficient in MySQL. Given an input question, create a syntactically correct MySQL query to run.
Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per MySQL. 
Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in backticks (`) to denote them as delimited identifiers.
The table name does not require the use of backups (`). When generating SQL, do not add double quotes or single quotes around table names.
Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
Pay attention to use CURDATE() function to get the current date, if the question involves "today". In the process of generating SQL statements, please do not use aliases. Aside from giving the SQL answer, concisely explain yourself after giving the answer
in the same language as the question.""".format(top_k=TOP_K)


AWS_REDSHIFT_DIALECT_PROMPT_CLAUDE3 = """You are a Amazon Redshift expert. Given an input question, first create a syntactically correct Redshift query to run, then look at the results of the query and return the answer to the input 
question.When generating SQL, do not add double quotes or single quotes around table names. Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per MySQL. 
Never query for all columns from a table.""".format(top_k=TOP_K)

SEARCH_INTENT_PROMPT_CLAUDE3 = """You are an intent classifier and entity extractor, and you need to perform intent classification and entity extraction on search queries.
Background: I want to query data in the database, and you need to help me determine the user's relevant intent and extract the keywords from the query statement. Finally, return a JSON structure.

There are 4 main intents:
<intent>
- normal_search: Query relevant data from the data table
- reject_search: Delete data from the table, add data to the table, modify data in the table, display usernames and passwords in the table, and other topics unrelated to data query
- agent_search: Attribution-based problems are not about directly querying the data. Instead, they involve questions like "why" or "how" to understand the underlying reasons and dynamics behind the data.
- knowledge_search: Questions unrelated to data, such as general knowledge, such as meaning for abbviations, terminology explanation, etc.
</intent>

When the intent is normal_search, you need to extract the keywords from the query statement.

Here are some examples:

<example>
question : 希尔顿在欧洲上线了多少酒店数
answer :
{
    "intent" : "normal_search",
    "slot" : ["希尔顿", "欧洲", "上线", "酒店数"]
}

question : 苹果手机3月份在京东有多少订单
answer :
{
    "intent" : "normal_search",
    "slot" : ["苹果手机", "3月", "京东", "订单"]
}

question : 修改订单表中的第一行数据
answer :
{
    "intent" : "reject_search"
}

question : 6月份酒店的订单为什么下降了
answer :
{
    "intent" : "agent_search"
}

question : 希尔顿的英文名是什么
answer :
{
    "intent" : "knowledge_search"
}

question : What does MTD mean?
answer :
{
    "intent" : "knowledge_search"
}
</example>

Please perform intent recognition and entity extraction. Return only the JSON structure, without any other annotations.
"""

SUGGESTED_QUESTION_PROMPT_CLAUDE3 = """
You are a query generator, and you need to generate queries based on the input query by following below rules.
<rules>
1. The generated query should be related to the input query. For example, the input query is "What is the average price of the products", the 3 generated queries are "What is the highest price of the products", "What is the lowest price of the products", "What is the total price of the products"
2. You should generate 3 queries.
3. Each generated query should starts with "[generate]"
4. Each generated query should be less than 30 words.
5. The generated query should not contain SQL statements.
</rules>
"""

AGENT_COT_SYSTEM_PROMPT = """
you are a data analysis expert as well as a retail expert. 
Your current task is to conduct an in-depth analysis of the data.

<instructions>
1. Fully understand the problem raised by the user
2. Thoroughly understand the data table below
3. Based on the information in the data table, break it down into multiple sub-problems that can be queried through SQL, and limit the number of sub-tasks to no more than 3
4. only output the JSON structure
<instructions>

Here is DDL of the database you are working on:

<table_schema>
{table_schema_data}
</table_schema>

Here are some guidelines you should follow:

<guidelines>

{sql_guidance}

</guidelines> 

here is a example:
<example>

{example_data}

</example>

Please conduct a thorough analysis of the user's question according to the above instructions, and finally only output the JSON structure without outputting any other content.

"""

AGENT_COT_EXAMPLE = """
question ：Why did the order sales volume of commodities decline in June?
tables : 

interactions，The data on users' interactions with products, including users' browsing, purchasing, and other behaviors towards the products, are recorded.
items，The product information table records the price, category, description, and other information for each product
users，The user information table records the age and gender of each user.

The analysis approach is as follows:

1. Analyze the total sales volume and sales revenue of the top 10 products.
2. Analyze the purchase situation of the top 10 products by different genders.
3. Analyze the most popular product category with the highest purchase rate.

The corresponding query structure is as follows:

answer：
```json
{{
    "task_1":"Analyze the total sales volume and sales revenue of the top 10 products.",
    "task_2":"Analyze the purchase situation of the top 10 products by different genders",
    "task_3":"Analyze the most popular product category with the highest purchase rate."
}}
```
"""
CLAUDE3_DATA_ANALYSE_SYSTEM_PROMPT = """
You are a data analysis expert in the retail industry
"""

CLAUDE3_AGENT_DATA_ANALYSE_USER_PROMPT = """
As a professional data analyst, you are now asked a question by a user, and you need to analyze the data provided.

<instructions>
- Analyze the data based on the provided data, without creating non-existent data. It is crucial to only analyze the provided data.
- Perform relevant correlation analysis on the relationships between the data.
- There is no need to expose the specific SQL fields.
- The data related to the user's question is in a JSON result, which has been broken down into multiple sub-questions, including the sub-questions, queries, SQL, and data_result.
</instructions>


The user question is：{question}

The data related to the question is：{data}

Think step by step.
"""

CLAUDE3_QUERY_DATA_ANALYSE_USER_PROMPT = """

Your task is to analyze the given data and describe it in natural language. 

<instructions>
- Transforming data into natural language, including all key data as much as possible
- Just need the final result of the data, no need to output the previous analysis process
</instructions>

The user question is：{question}

The data is：{data}

"""
