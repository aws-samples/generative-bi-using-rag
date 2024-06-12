import json
import os
import traceback
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

from nlq.business.connection import ConnectionManagement
from nlq.business.profile import ProfileManagement
from utils.llm import get_query_intent
from utils.tool import generate_log_id, get_current_time
from .enum import ContentEnum, ErrorEnum
from .schemas import Question, QuestionSocket, Answer, Option, CustomQuestion, SQLSearchResult, \
    AgentSearchResult, KnowledgeSearchResult, TaskSQLSearchResult, FeedBackInput, ChartEntity
from . import service
from nlq.business.nlq_chain import NLQChain
from dotenv import load_dotenv

from .service import ask_websocket

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/qa", tags=["qa"])
load_dotenv()


@router.get("/option", response_model=Option)
def option():
    return service.get_option()


@router.get("/get_custom_question", response_model=CustomQuestion)
def get_custom_question(data_profile: str):
    all_profiles = ProfileManagement.get_all_profiles_with_info()
    comments = all_profiles[data_profile]['comments']
    comments_questions = []
    if len(comments.split("Examples:")) > 1:
        comments_questions_txt = comments.split("Examples:")[1]
        comments_questions = [i for i in comments_questions_txt.split("\n") if i != '']
    custom_question = CustomQuestion(custom_question=comments_questions)
    return custom_question


@router.post("/ask", response_model=Answer)
def ask(question: Question):
    return service.ask(question)


@router.post("/ask/test", response_model=Answer)
def ask_mock_bar(question_type: str):
    if question_type == "normal_table":
        mock_data = {
            'query': '40岁以上男性用户浏览次数最多的前3个商品类别是什么',
            'query_intent': 'normal_search',
            'knowledge_search_result': {
                'knowledge_response': ''
            },
            'sql_search_result': {
                'sql': "\nSELECT\n `category_l1`,\n `category_l2`,\n COUNT(*) AS view_count\nFROM\n `interactions` i\nJOIN\n `items` p ON i.`item_id` = p.`item_id`\nJOIN\n `users` u ON i.`user_id` = u.`user_id`\nWHERE\n u.`gender` = 'M'\n AND u.`age` >= 40\n AND i.`event_type` = 'View'\nGROUP BY\n `category_l1`, `category_l2`\nORDER BY\n view_count DESC\nLIMIT 3;\n",
                'sql_data': [
                    ['category_l1', 'category_l2', 'view_count'],
                    ['housewares', 'kitchen', 8334],
                    ['apparel', 'jacket', 3748],
                    ['seasonal', 'christmas', 3559]
                ],
                'data_show_type': 'table',
                'sql_gen_process': '\n\n这个查询首先连接了 interactions、items 和 users 三个表，以获取用户浏览商品的信息以及用户的年龄和性别。然后通过 WHERE 子句过滤出男性且年龄大于等于 40 岁的用户,并且只考虑浏览事件。接着按照商品的一级和二级分类进行分组,计算每个分类的浏览次数。最后按照浏览次数降序排列,并限制输出前 3 条记录,即为浏览次数最多的前 3 个商品类别。',
                'data_analyse': '根据给定的数据,40岁以上男性用户浏览次数最多的前3个商品类别分别是:\n\n1. 家居用品类别下的厨房用品,浏览次数为8334次。\n\n2. 服装类别下的夹克,浏览次数为3748次。 \n\n3. 季节性商品类别下的圣诞节用品,浏览次数为3559次。'
            },
            'agent_search_result': {
                'sub_search_task': [],
                'agent_sql_search_result': [],
                'agent_summary': ''
            },
            'suggested_question': [
                '40岁以上女性用户浏览次数最多的前3个商品类别是什么',
                '30岁以下男性用户浏览次数最多的前3个商品类别是什么', '30岁以上用户浏览次数最少的商品类别是什么']
        }
        sql_search_result = SQLSearchResult(
            sql_data=mock_data["sql_search_result"]["sql_data"],
            sql=mock_data["sql_search_result"]["sql"],
            data_show_type=mock_data["sql_search_result"]["data_show_type"],
            sql_gen_process=mock_data["sql_search_result"]["sql_gen_process"],
            data_analyse=mock_data["sql_search_result"]["data_analyse"])

        agent_search_response = AgentSearchResult(agent_summary="", agent_sql_search_result=[], sub_search_task=[])

        knowledge_search_result = KnowledgeSearchResult(knowledge_response="")
        answer = Answer(query=mock_data["query"], query_intent="normal_search",
                        knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=mock_data['suggested_question'])
        return answer
    elif question_type == "normal_bar":
        mock_data = {
            'query': '男性和女性用户中有多少人完成了购买',
            'query_intent': 'normal_search',
            'knowledge_search_result': {
                'knowledge_response': ''
            },
            'sql_search_result': {
                'sql': "\nSELECT \n    `gender`,\n    COUNT(DISTINCT `user_id`) AS num_users\nFROM\n    `users`\nWHERE\n    `user_id` IN (\n        SELECT\n            `user_id`\n        FROM\n            `interactions`\n        WHERE\n            `event_type` = 'Purchase'\n    )\nGROUP BY\n    `gender`\nLIMIT 100;\n",
                'sql_data': [
                    ['gender', 'num_users'],
                    ['F', 1906],
                    ['M', 1788]
                ],
                'data_show_type': 'bar',
                'sql_gen_process': "\n\n这个查询首先从 `interactions` 表中找出所有进行过 'Purchase' 事件的 `user_id`。然后在 `users` 表中根据这些 `user_id` 统计男性和女性用户的数量。通过 GROUP BY `gender` 将结果按性别分组,并使用 COUNT(DISTINCT `user_id`) 来计算每个性别中不重复的用户数量。",
                'data_analyse': '根据给定的数据,我们可以总结如下:\n\n在所有用户中,有1906名女性用户和1788名男性用户。因此,在完成购买的用户中,女性用户人数略多于男性用户。具体来说,女性用户占总用户数的51.6%,而男性用户占48.4%。'
            },
            'agent_search_result': {
                'sub_search_task': [],
                'agent_sql_search_result': [],
                'agent_summary': ''
            },
            'suggested_question': []
        }
        sql_search_result = SQLSearchResult(sql_data=mock_data["sql_search_result"]["sql_data"],
                                            sql=mock_data["sql_search_result"]["sql"],
                                            data_show_type=mock_data["sql_search_result"]["data_show_type"],
                                            sql_gen_process=mock_data["sql_search_result"]["sql_gen_process"],
                                            data_analyse=mock_data["sql_search_result"]["data_analyse"])

        agent_search_response = AgentSearchResult(agent_summary="", agent_sql_search_result=[], sub_search_task=[])

        knowledge_search_result = KnowledgeSearchResult(knowledge_response="")
        answer = Answer(query=mock_data["query"], query_intent="normal_search",
                        knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=["男性最喜欢的购买类别是什么", "女性最喜欢的购买类别是什么",
                                            "女性最喜欢的购买类别是什么"])
        return answer
    elif question_type == "normal_line":
        mock_data = {
            'query': '销量前10的商品是什么，输出商品id和销量',
            'query_intent': 'normal_search',
            'knowledge_search_result': {
                'knowledge_response': ''
            },
            'sql_search_result': {
                'sql': "\nSELECT \n `item_id`, \n COUNT(`user_id`) AS sales_count\nFROM \n `interactions`\nWHERE\n `event_type` = 'Purchase'\nGROUP BY\n `item_id`\nORDER BY \n sales_count DESC\nLIMIT 10;\n",
                'sql_data': [
                    ['item_id', 'sales_count'],
                    ['0790267c-c708-424d-81f5-46903a9c8444', 65],
                    ['575c0ac0-5494-4c64-a886-a9c0cf8b779a', 48],
                    ['b20ba076-58a7-4602-9b56-4bee46e98388', 46],
                    ['aff05423-76e8-4339-a478-fc17d51ed985', 44],
                    ['0987bfa1-0a23-4b90-8882-8a6e9bd91e24', 42],
                    ['a6f43f84-a89a-446f-8adc-8b1a23a30a81', 21],
                    ['24c62ad2-6977-4f69-be75-e37d897c1434', 20],
                    ['9c1a2048-7aac-4565-b836-d8d4f726322c', 16],
                    ['4496471c-b098-4915-9a1a-8b9e60043737', 14],
                    ['5afced84-ed2d-4520-a06d-dcfeab382e52', 14]
                ],
                'data_show_type': 'line',
                'sql_gen_process': "\n\n这个查询首先从 `interactions` 表中选择出所有 `event_type` 为 'Purchase' 的记录，这代表用户购买了商品。然后按照 `item_id` 对购买记录进行分组计数，得到每个商品的销量。最后按销量降序排列并限制输出前 10 行记录，包含了商品 ID 和对应的销量数。",
                'data_analyse': '根据给定的数据,销量前10的商品及其销量如下:\n\n1. 商品ID为0790267c-c708-424d-81f5-46903a9c8444的商品,销量为65件。\n2. 商品ID为575c0ac0-5494-4c64-a886-a9c0cf8b779a的商品,销量为48件。 \n3. 商品ID为b20ba076-58a7-4602-9b56-4bee46e98388的商品,销量为46件。\n4. 商品ID为aff05423-76e8-4339-a478-fc17d51ed985的商品,销量为44件。\n5. 商品ID为0987bfa1-0a23-4b90-8882-8a6e9bd91e24的商品,销量为42件。\n6. 商品ID为a6f43f84-a89a-446f-8adc-8b1a23a30a81的商品,销量为21件。\n7. 商品ID为24c62ad2-6977-4f69-be75-e37d897c1434的商品,销量为20件。\n8. 商品ID为9c1a2048-7aac-4565-b836-d8d4f726322c的商品,销量为16件。\n9. 商品ID为4496471c-b098-4915-9a1a-8b9e60043737的商品,销量为14件。 \n10. 商品ID为5afced84-ed2d-4520-a06d-dcfeab382e52的商品,销量为14件。'
            },
            'agent_search_result': {
                'sub_search_task': [],
                'agent_sql_search_result': [],
                'agent_summary': ''
            },
            'suggested_question': []
        }
        sql_search_result = SQLSearchResult(
            sql_data=mock_data["sql_search_result"]["sql_data"],
            sql=mock_data["sql_search_result"]["sql"],
            data_show_type=mock_data["sql_search_result"]["data_show_type"],
            sql_gen_process=mock_data["sql_search_result"]["sql_gen_process"],
            data_analyse=mock_data["sql_search_result"]["data_analyse"])

        agent_search_response = AgentSearchResult(agent_summary="", agent_sql_search_result=[], sub_search_task=[])

        knowledge_search_result = KnowledgeSearchResult(knowledge_response="")
        answer = Answer(query=mock_data["query"], query_intent="normal_search",
                        knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=["男性最喜欢的购买类别是什么", "女性最喜欢的购买类别是什么",
                                            "女性最喜欢的购买类别是什么"])
        return answer
    elif question_type == "normal_pie":
        mock_data = {
            'query': '男性和女性用户中有多少人完成了购买',
            'query_intent': 'normal_search',
            'knowledge_search_result': {
                'knowledge_response': ''
            },
            'sql_search_result': {
                'sql': "\nSELECT \n    `gender`,\n    COUNT(DISTINCT `user_id`) AS num_users\nFROM\n    `users`\nWHERE\n    `user_id` IN (\n        SELECT\n            `user_id`\n        FROM\n            `interactions`\n        WHERE\n            `event_type` = 'Purchase'\n    )\nGROUP BY\n    `gender`\nLIMIT 100;\n",
                'sql_data': [
                    ['gender', 'num_users'],
                    ['F', 1906],
                    ['M', 1788]
                ],
                'data_show_type': 'pie',
                'sql_gen_process': "\n\n这个查询首先从 `interactions` 表中找出所有进行过 'Purchase' 事件的 `user_id`。然后在 `users` 表中根据这些 `user_id` 统计男性和女性用户的数量。通过 GROUP BY `gender` 将结果按性别分组,并使用 COUNT(DISTINCT `user_id`) 来计算每个性别中不重复的用户数量。",
                'data_analyse': '根据给定的数据,我们可以总结如下:\n\n在所有用户中,有1906名女性用户和1788名男性用户。因此,在完成购买的用户中,女性用户人数略多于男性用户。具体来说,女性用户占总用户数的51.6%,而男性用户占48.4%。'
            },
            'agent_search_result': {
                'sub_search_task': [],
                'agent_sql_search_result': [],
                'agent_summary': ''
            },
            'suggested_question': []
        }
        sql_search_result = SQLSearchResult(
            sql_data=mock_data["sql_search_result"]["sql_data"],
            sql=mock_data["sql_search_result"]["sql"],
            data_show_type=mock_data["sql_search_result"]["data_show_type"],
            sql_gen_process=mock_data["sql_search_result"]["sql_gen_process"],
            data_analyse=mock_data["sql_search_result"]["data_analyse"])

        agent_search_response = AgentSearchResult(agent_summary="", agent_sql_search_result=[], sub_search_task=[])

        knowledge_search_result = KnowledgeSearchResult(knowledge_response="")
        answer = Answer(query=mock_data["query"], query_intent="normal_search",
                        knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=["男性最喜欢的购买类别是什么", "女性最喜欢的购买类别是什么",
                                            "女性最喜欢的购买类别是什么"])
        return answer
    elif question_type == "agent":
        mock_data = {
            'query': '为什么销量下降了，分析一下商品的销售下降的原因',
            'query_intent': 'agent_search',
            'knowledge_search_result': {
                'knowledge_response': ''
            },
            'sql_search_result': {
                'sql': '',
                'sql_data': [],
                'data_show_type': 'table',
                'sql_gen_process': '',
                'data_analyse': ''
            },
            'agent_search_result': {
                'agent_sql_search_result': [{
                    'sub_task_query': '分析不同时间段的商品总销售量和销售收入的变化趋势',
                    'sql': "\nSELECT\n    DATE_FORMAT(`timestamp`, '%Y-%m') AS month_year,\n    COUNT(DISTINCT CASE WHEN `event_type` = 'Purchase' THEN `inter`.`item_id` END) AS total_purchases,\n    SUM(CASE WHEN `event_type` = 'Purchase' THEN `i`.`price` END) AS total_revenue\nFROM\n    `interactions` AS `inter`\nJOIN\n    `items` AS `i` ON `inter`.`item_id` = `i`.`item_id`\nGROUP BY\n    month_year\nORDER BY\n    month_year\nLIMIT 100;\n",
                    'sql_data': [
                        ['month_year', 'total_purchases', 'total_revenue'],
                        ['2023-12', 2162, 617303.8590472937]
                    ],
                    'data_show_type': 'table',
                    'sql_gen_process': '',
                    'data_analyse': ''
                }, {
                    'sub_task_query': '分析促销商品和非促销商品的销售量和销售收入对比',
                    'sql': "\nSELECT\n    `promoted`,\n    COUNT(DISTINCT CASE WHEN `event_type` = 'Purchase' THEN `inter`.`item_id` END) AS num_purchases,\n    SUM(CASE WHEN `event_type` = 'Purchase' THEN `i`.`price` END) AS revenue\nFROM\n    `interactions` AS `inter`\nJOIN\n    `items` AS `i` ON `inter`.`item_id` = `i`.`item_id`\nGROUP BY\n    `promoted`\nLIMIT 100;\n",
                    'sql_data': [
                        ['promoted', 'num_purchases', 'revenue'],
                        ['F', 9, 707.0],
                        ['N', 1594, 466924.7089368105],
                        ['Y', 531, 147015.8301193714]
                    ],
                    'data_show_type': 'table',
                    'sql_gen_process': '',
                    'data_analyse': ''
                }],
                'agent_summary': '根据提供的数据和问题"为什么销量下降了，分析一下商品的销售下降的原因"，我们可以进行以下分析:\n\n1. 分析不同时间段的商品总销售量和销售收入的变化趋势。\n\n根据第一个查询的结果，我们可以看到每个月的总购买量和总销售收入。通过对比不同月份的数据变化,可以发现销售量和收入是否出现了下降的趋势。如果出现了下降,我们可以进一步分析下降的时间段。\n\n2. 分析促销商品和非促销商品的销售量和销售收入对比。\n\n根据第二个查询的结果,我们可以比较促销商品和非促销商品的购买量和销售收入。如果促销商品的销售表现较差,可能意味着促销活动效果不佳,导致整体销量下降。相反,如果非促销商品的销售表现较差,则可能需要分析其他原因。\n\n3. 进一步分析可能影响销量的其他因素。\n\n除了时间趋势和促销活动外,还可以分析其他可能影响销量的因素,例如商品类别、价格区间、地理位置等。通过对这些因素进行分组统计和对比,或许能发现销量下降的潜在原因。\n\n总的来说,通过分析不同时间段的销售趋势、促销活动效果,以及其他可能的影响因素,我们可以对商品销售下降的原因有一个初步的了解。当然,实际情况可能更加复杂,需要结合更多的数据和上下文信息进行综合分析。'
            },
            'suggested_question': []
        }

        sql_search_result = SQLSearchResult(query=mock_data["query"], sql_data=[], sql="", data_show_type="table",
                                            sql_gen_process="",
                                            data_analyse="")

        agent_search_response = AgentSearchResult(agent_summary="", agent_sql_search_result=[], sub_search_task=[])
        agent_search_response.agent_summary = mock_data["agent_search_result"]["agent_summary"]
        agent_search_response.sub_search_task = mock_data["agent_search_result"]["sub_search_task"]

        sql_search_result_one = TaskSQLSearchResult(
            sub_task_query=mock_data["agent_search_result"]["agent_sql_search_result"][0]["sub_task_query"],
            sql_data=mock_data["agent_search_result"]["agent_sql_search_result"][0]["sql_data"],
            sql=mock_data["agent_search_result"]["agent_sql_search_result"][0]["sql"],
            data_show_type=mock_data["agent_search_result"]["agent_sql_search_result"][0]["data_show_type"],
            sql_gen_process="",
            data_analyse="")

        sql_search_result_two = TaskSQLSearchResult(
            sub_task_query=mock_data["agent_search_result"]["agent_sql_search_result"][1]["sub_task_query"],
            sql_data=mock_data["agent_search_result"]["agent_sql_search_result"][1]["sql_data"],
            sql=mock_data["agent_search_result"]["agent_sql_search_result"][1]["sql"],
            data_show_type=mock_data["agent_search_result"]["agent_sql_search_result"][1]["data_show_type"],
            sql_gen_process="",
            data_analyse="")

        agent_search_response.agent_sql_search_result = [sql_search_result_one, sql_search_result_two]
        knowledge_search_result = KnowledgeSearchResult(knowledge_response="")

        answer = Answer(query=mock_data["query"], query_intent="agent_search",
                        knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=["男性最喜欢的购买类别是什么", "女性最喜欢的购买类别是什么",
                                            "女性最喜欢的购买类别是什么"])
        return answer

    elif question_type == "knowledge":

        mock_data = {
            'query': '什么是WTD',
            'query_intent': 'knowledge_search',
            'knowledge_search_result': {
                'knowledge_response': 'Based on the provided context, WTD stands for "Week to Date". The comment explains that "It\'s the period starting from the beginning of the current week up until now, but not including today\'s date, because it might not be complete yet. The week starts on Monday."\n\n'
            },
            'sql_search_result': {
                'sql': '',
                'sql_data': [],
                'data_show_type': 'table',
                'sql_gen_process': '',
                'data_analyse': ''
            },
            'agent_search_result': {
                'sub_search_task': [],
                'agent_sql_search_result': [],
                'agent_summary': ''
            },
            'suggested_question': []
        }
        sql_search_result = SQLSearchResult(sql_data=[], sql="", data_show_type="table",
                                            sql_gen_process="",
                                            data_analyse="")

        agent_search_response = AgentSearchResult(agent_summary="", agent_sql_search_result=[], sub_search_task=[])

        knowledge_search_result = KnowledgeSearchResult(knowledge_response="")

        knowledge_search_result.knowledge_response = mock_data["knowledge_search_result"]["knowledge_response"]

        answer = Answer(query=mock_data["query"], query_intent="knowledge_search",
                        knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=["男性最喜欢的购买类别是什么", "女性最喜欢的购买类别是什么",
                                            "女性最喜欢的购买类别是什么"])
        return answer
    else:
        sql_search_result = SQLSearchResult(sql_data=[], sql="", data_show_type="table",
                                            sql_gen_process="",
                                            data_analyse="")

        agent_search_response = AgentSearchResult(agent_summary="", agent_sql_search_result=[], sub_search_task=[])

        knowledge_search_result = KnowledgeSearchResult(knowledge_response="")

        answer = Answer(query="今天天气怎么呀", query_intent="reject_search",
                        knowledge_search_result=knowledge_search_result,
                        sql_search_result=sql_search_result, agent_search_result=agent_search_response,
                        suggested_question=[])
        return answer


@router.post("/user_feedback")
def user_feedback(input_data: FeedBackInput):
    feedback_type = input_data.feedback_type
    if feedback_type == "upvote":
        upvote_res = service.user_feedback_upvote(input_data.data_profiles, input_data.query,
                                                  input_data.query_intent, input_data.query_answer)
        return upvote_res
    else:
        downvote_res = service.user_feedback_downvote(input_data.data_profiles, input_data.query,
                                                      input_data.query_intent, input_data.query_answer)
        return downvote_res


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                question_json = json.loads(data)
                question = QuestionSocket(**question_json)
                session_id = question.session_id
                await ask_websocket(websocket, question)


            #     current_nlq_chain = service.get_nlq_chain(question)
            #     if question.use_rag:
            #         examples = service.get_example(current_nlq_chain)
            #         await response_websocket(websocket, session_id, "Examples:\n```json\n")
            #         await response_websocket(websocket, session_id, str(examples))
            #         await response_websocket(websocket, session_id, "\n```\n")
            #     response = service.ask_with_response_stream(question, current_nlq_chain)
            #     if os.getenv('SAGEMAKER_ENDPOINT_SQL', ''):
            #         await response_sagemaker_sql(websocket, session_id, response, current_nlq_chain)
            #         await response_websocket(websocket, session_id, "\n")
            #         explain_response = service.explain_with_response_stream(current_nlq_chain)
            #         await response_sagemaker_explain(websocket, session_id, explain_response)
            #     else:
            #         await response_bedrock(websocket, session_id, response, current_nlq_chain)
            #
            #     if question.query_result:
            #         final_sql_query_result = service.get_executed_result(current_nlq_chain)
            #         await response_websocket(websocket, session_id, "\n\nQuery result:  \n")
            #         await response_websocket(websocket, session_id, final_sql_query_result)
            #         await response_websocket(websocket, session_id, "\n")
            #     await response_websocket(websocket, session_id, "", ContentEnum.END)
            except Exception:
                msg = traceback.format_exc()
                logger.exception(msg)
                await response_websocket(websocket, session_id, msg, ContentEnum.EXCEPTION)
    except WebSocketDisconnect:
        logger.info(f"{websocket.client.host} disconnected.")


async def response_sagemaker_sql(websocket: WebSocket, session_id: str, response: dict, current_nlq_chain: NLQChain):
    result_pieces = []
    for event in response['Body']:
        current_body = event["PayloadPart"]["Bytes"].decode('utf8')
        result_pieces.append(current_body)
        await response_websocket(websocket, session_id, current_body)
    # TODO Must modify response
    sql_response = '''<query>SELECT i.`item_id`, i.`product_description`, COUNT(it.`event_type`) AS total_purchases
FROM `items` i
JOIN `interactions` it ON i.`item_id` = it.`item_id`
WHERE it.`event_type` = 'purchase'
GROUP BY i.`item_id`, i.`product_description`
ORDER BY total_purchases DESC
LIMIT 10;</query>'''
    current_nlq_chain.set_generated_sql_response(sql_response)


async def response_sagemaker_explain(websocket: WebSocket, session_id: str, response: dict):
    for event in response['Body']:
        current_body = event["PayloadPart"]["Bytes"].decode('utf8')
        current_content = json.loads(current_body)
        await response_websocket(websocket, session_id, current_content.get("outputs"))


async def response_bedrock(websocket: WebSocket, session_id: str, response: dict, current_nlq_chain: NLQChain):
    result_pieces = []
    for event in response['body']:
        current_body = event["chunk"]["bytes"].decode('utf8')
        current_content = json.loads(current_body)
        if current_content.get("type") == "content_block_delta":
            current_text = current_content.get("delta").get("text")
            result_pieces.append(current_text)
            await response_websocket(websocket, session_id, current_text)
        elif current_content.get("type") == "content_block_stop":
            break
    current_nlq_chain.set_generated_sql_response(''.join(result_pieces))


async def response_websocket(websocket: WebSocket, session_id: str, content: str,
                             content_type: ContentEnum = ContentEnum.COMMON):
    content_obj = {
        "session_id": session_id,
        "content_type": content_type.value,
        "content": content,
    }
    final_content = json.dumps(content_obj)
    await websocket.send_text(final_content)
