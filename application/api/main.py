from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from .schemas import Question, Answer
from . import service

router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("/ask", response_model=Answer)
def ask(question: Question):
    return service.ask(question)

