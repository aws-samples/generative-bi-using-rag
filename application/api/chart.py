# -*- coding:utf-8 -*-
# @FileName  : chart.py
# @Time      : 2024/7/19 14:53
# @Author    : dingtianlu
# @Function  :
import json
import logging
import traceback
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Depends, Cookie, HTTPException

from api.dlset_service import dlset_ask_websocket
from api.enum import ContentEnum
from api.schemas import DlsetQuestion
from utils.validate import validate_token, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dlset", tags=["superset"])
load_dotenv()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, dlunifiedtoken: Optional[str] = Cookie(None)):
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
            question = DlsetQuestion(**question_json)
            user_id = question.user_id
            session_id = question.session_id
            try:
                jwt_token = question_json.get('token', None)
                answer = {}
                if jwt_token:
                    del question_json['token']
                    res = validate_token(jwt_token)
                    if not res['success']:
                        answer['X-Status-Code'] = status.HTTP_401_UNAUTHORIZED
                        await response_websocket(websocket=websocket, session_id=session_id, content=answer,
                                                 content_type=ContentEnum.END, user_id=user_id)
                    else:
                        ask_result = await dlset_ask_websocket(websocket, question)
                        logger.info(ask_result)
                        answer = ask_result.dict()
                        await response_websocket(websocket=websocket, session_id=session_id, content=answer,
                                                 content_type=ContentEnum.END, user_id=user_id)
                else:
                    answer['X-Status-Code'] = status.HTTP_401_UNAUTHORIZED
                    await response_websocket(websocket=websocket, session_id=session_id, content=answer,
                                             content_type=ContentEnum.END, user_id=user_id)
            except Exception as e:
                logger.error(e)
                msg = traceback.format_exc()
                logger.exception(msg)
                await response_websocket(websocket=websocket, session_id=session_id, content=msg,
                                         content_type=ContentEnum.EXCEPTION, user_id=user_id)
    except WebSocketDisconnect:
        logger.info(f"{websocket.client.host} disconnected.")


async def response_websocket(websocket: WebSocket, session_id: str, content,
                             content_type: ContentEnum = ContentEnum.COMMON, status: str = "-1", user_id: str = "admin"):
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