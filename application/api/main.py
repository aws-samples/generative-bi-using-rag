import json
import os
import traceback
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from .enum import ContentEnum, ErrorEnum
from .schemas import Question, QuestionSocket, Answer, Option, CustomQuestion
from . import service
from nlq.business.nlq_chain import NLQChain
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/qa", tags=["qa"])
load_dotenv()


@router.get("/option", response_model=Option)
def option():
    return service.get_option()

@router.get("/get_custom_question", response_model= CustomQuestion)
def get_custom_question():
    question_list = ["销量前十的商品是什么" , "用户的平均年龄是多少", "商品的平均价格是多少"]
    custom_question = CustomQuestion(custom_question = question_list)
    return custom_question


@router.post("/ask", response_model=Answer)
def ask(question: Question):
    return service.ask(question)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                question_json = json.loads(data)
                question = QuestionSocket(**question_json)
                logger.info(question)
                session_id = question.session_id
                if not session_id:
                    await response_websocket(websocket, session_id, ErrorEnum.INVAILD_SESSION_ID.get_message(), ContentEnum.EXCEPTION)
                    continue
                current_nlq_chain = service.get_nlq_chain(question)
                if question.use_rag:
                    examples = service.get_example(current_nlq_chain)
                    await response_websocket(websocket, session_id, "Examples:\n```json\n")
                    await response_websocket(websocket, session_id, str(examples))
                    await response_websocket(websocket, session_id, "\n```\n")
                response = service.ask_with_response_stream(question, current_nlq_chain)
                if os.getenv('SAGEMAKER_ENDPOINT_SQL',''):
                    await response_sagemaker_sql(websocket, session_id, response, current_nlq_chain)
                    await response_websocket(websocket, session_id, "\n")
                    explain_response = service.explain_with_response_stream(current_nlq_chain)
                    await response_sagemaker_explain(websocket, session_id, explain_response)
                else:
                    await response_bedrock(websocket, session_id, response, current_nlq_chain)
                
                if question.query_result:
                    final_sql_query_result = service.get_executed_result(current_nlq_chain)
                    await response_websocket(websocket, session_id, "\n\nQuery result:  \n")
                    await response_websocket(websocket, session_id, final_sql_query_result)
                    await response_websocket(websocket, session_id, "\n")
                await response_websocket(websocket, session_id, "", ContentEnum.END)
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


async def response_websocket(websocket: WebSocket, session_id: str, content: str, content_type: ContentEnum=ContentEnum.COMMON):
    content_obj = {
        "session_id": session_id,
        "content_type": content_type.value,
        "content": content,
    }
    final_content = json.dumps(content_obj)
    await websocket.send_text(final_content)
