import json
import traceback
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, HTTPException, Cookie
import logging

from nlq.business.log_store import LogManagement
from nlq.business.profile import ProfileManagement
from utils.validate import validate_token, get_current_user
from .enum import ContentEnum
from .schemas import Question, Answer, Option, CustomQuestion, FeedBackInput, HistoryRequest, Message, HistoryMessage, \
    DlsetMessage, DlsetHistoryMessage, HistorySessionRequest
from . import service
from nlq.business.nlq_chain import NLQChain
from dotenv import load_dotenv
import base64

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


@router.post("/get_history_by_user_profile")
def get_history_by_user_profile(history_request: HistoryRequest):
    user_id = history_request.user_id
    profile_name = history_request.profile_name
    log_type = history_request.log_type
    user_id = base64.b64decode(user_id).decode('utf-8')
    history_list = LogManagement.get_history(user_id, profile_name, log_type)
    chat_history = format_chat_history(history_list, log_type)
    return chat_history


def format_chat_history(history_list, log_type):
    chat_history = []
    chat_history_session = {}
    for item in history_list:
        session_id = item['session_id']
        query = item['query']
        if session_id not in chat_history_session:
            chat_history_session[session_id] = {
                "history": [],
                "title": query
            }
        log_info = item['log_info']
        if log_type == 'superset':
            human_message = DlsetMessage(type="human", content=query)
            bot_message = DlsetMessage(type="AI", content=json.loads(log_info))
        else:
            human_message = Message(type="human", content=query)
            bot_message = Message(type="AI", content=json.loads(log_info))
        chat_history_session[session_id]['history'].append(human_message)
        chat_history_session[session_id]['history'].append(bot_message)
    for key, value in chat_history_session.items():
        if log_type == 'superset':
            each_session_history = DlsetHistoryMessage(session_id=key, messages=value['history'], title=value['title'])
        else:
            each_session_history = HistoryMessage(session_id=key, messages=value['history'], title=value['title'])
        chat_history.append(each_session_history)
    return chat_history


@router.post("/user_feedback")
def user_feedback(input_data: FeedBackInput):
    feedback_type = input_data.feedback_type
    user_id = input_data.user_id
    session_id = input_data.session_id
    if feedback_type == "upvote":
        upvote_res = service.user_feedback_upvote(input_data.data_profiles, user_id, session_id, input_data.query,
                                                  input_data.query_intent, input_data.query_answer)
        return upvote_res
    else:
        downvote_res = service.user_feedback_downvote(input_data.data_profiles, user_id, session_id, input_data.query,
                                                      input_data.query_intent, input_data.query_answer)
        return downvote_res


@router.post("/get_sessions")
def get_sessions(history_request: HistoryRequest):
    user_id = base64.b64decode(history_request.user_id).decode('utf-8')
    return LogManagement.get_all_sessions(user_id, history_request.profile_name, history_request.log_type)


@router.post("/get_history_by_session")
def get_history_by_session(history_request: HistorySessionRequest):
    user_id = base64.b64decode(history_request.user_id).decode('utf-8')
    history_list = LogManagement.get_all_history_by_session(profile_name=history_request.profile_name, user_id=user_id,
                                                            session_id=history_request.session_id,
                                                            size=1000, log_type=history_request.log_type)
    chat_history = format_chat_history(history_list, history_request.log_type)
    return chat_history

@router.post("/delete_history_by_session")
def delete_history_by_session(history_request: HistorySessionRequest):
    user_id = history_request.user_id
    profile_name = history_request.profile_name
    session_id = history_request.session_id
    return LogManagement.delete_history_by_session(user_id, profile_name, session_id)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, dlunifiedtoken: Optional[str] = Cookie(None)):
    print('---WEB SOCKET---', vars(websocket))
    try:
        get_current_user(dlunifiedtoken)
    except HTTPException as e:
        await websocket.close(code=1008, reason=e.detail)  # 关闭连接，代码1008表示违反策略
        return
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            question_json = json.loads(data)
            question = Question(**question_json)
            session_id = question.session_id
            user_id = base64.b64decode(question.user_id).decode('utf-8')
            try:
                jwt_token = question_json.get('dlunifiedtoken', None)
                if jwt_token:
                    del question_json['dlunifiedtoken']

                print('---JWT TOKEN---', jwt_token)

                if jwt_token:
                    res = validate_token(jwt_token)
                    if not res["success"]:
                        answer = {}
                        answer['X-Status-Code'] = status.HTTP_401_UNAUTHORIZED
                        await response_websocket(websocket=websocket, session_id=session_id, content=answer,
                                                 content_type=ContentEnum.END, user_id=user_id)
                    else:
                        ask_result = await ask_websocket(websocket, question)
                        logger.info(ask_result)
                        answer = ask_result.dict()
                        answer['X-Status-Code'] = 200
                        answer['X-User-Id'] = base64.b64encode(res['user_id'].encode('utf-8')).decode('utf-8')
                        answer['X-User-Name'] = base64.b64encode(res['user_name'].encode('utf-8')).decode('utf-8')
                        await response_websocket(websocket=websocket, session_id=session_id, content=answer,
                                                 content_type=ContentEnum.END, user_id=user_id)
                else:
                    answer = {}
                    answer['X-Status-Code'] = status.HTTP_401_UNAUTHORIZED
                    await response_websocket(websocket=websocket, session_id=session_id, content=answer,
                                             content_type=ContentEnum.END, user_id=user_id)
            except Exception:
                msg = traceback.format_exc()
                logger.exception(msg)
                await response_websocket(websocket=websocket, session_id=session_id, content=msg,
                                         content_type=ContentEnum.EXCEPTION, user_id=user_id)
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
    final_content = json.dumps(content_obj)
    await websocket.send_text(final_content)
