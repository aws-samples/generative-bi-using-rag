import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from .schemas import Question, Answer, Option
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
            question_json = json.loads(data)
            question = Question(**question_json)
            logger.info(question)
            current_nlq_chain = service.get_nlq_chain(question)
            if question.use_rag:
                examples = service.get_example(current_nlq_chain)
                await websocket.send_text("Examples:\n```json\n")
                await websocket.send_text(str(examples))
                await websocket.send_text("\n```\n")
            response = service.ask_with_response_stream(question, current_nlq_chain)
            result_pieces = []
            for event in response['body']:
                final_answer = event["chunk"]["bytes"].decode('utf8')
                # logger.info(final_answer)
                current_content = json.loads(final_answer)
                if current_content.get("type") == "content_block_delta":
                    current_text = current_content.get("delta").get("text")
                    result_pieces.append(current_text)
                    await websocket.send_text(current_text)
                elif current_content.get("type") == "content_block_stop":
                    break
            current_nlq_chain.set_generated_sql_response(''.join(result_pieces))
            if question.query_result:
                final_sql_query_result = service.get_executed_result(current_nlq_chain)
                await websocket.send_text("\n\nQuery result:  \n")
                await websocket.send_text(final_sql_query_result)
                await websocket.send_text("\n")
    except WebSocketDisconnect:
        logger.info(f"{websocket.client.host} disconnected.")
