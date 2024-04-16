import json
import traceback
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from .enum import ContentEnum, ErrorEnum
from .schemas import Question, QuestionSocket, Answer, Option
from . import service

router = APIRouter(prefix="/qa", tags=["qa"])


@router.get("/option", response_model=Option)
def option():
    return service.get_option()


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


async def response_websocket(websocket: WebSocket, session_id: str, content: str, content_type: ContentEnum=ContentEnum.COMMON):
    content_obj = {
        "session_id": session_id,
        "content_type": content_type.value,
        "content": content,
    }
    final_content = json.dumps(content_obj)
    await websocket.send_text(final_content)
