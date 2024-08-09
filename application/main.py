import json
import logging

from fastapi import FastAPI, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response
from api.exception_handler import biz_exception
from api.main import router
from fastapi.middleware.cors import CORSMiddleware
from api import service
from api.schemas import Option, Message
from nlq.business.log_store import LogManagement
from utils.tool import set_share_data, get_share_data
from utils.auth import authenticate

MAX_CHAT_WINDOW_SIZE = 10 * 2
app = FastAPI(title='GenBI')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.middleware("http")
async def http_authenticate(request: Request, call_next):
    print('---HTTP REQUEST---', vars(request), request.cookies)
    access_token = request.headers.get("X-Access-Token")
    id_token = request.headers.get("X-Id-Token")
    refresh_token = request.headers.get("X-Refresh-Token")

    response = authenticate(access_token, id_token, refresh_token)

    if response["X-Status-Code"] != status.HTTP_200_OK:
        return Response(status_code=response["X-Status-Code"])
    else:
        access_token = response["X-Access-Token"]
        id_token = response["X-Id-Token"]
        username = response["X-User-Name"]
        email = response["X-Email"]
        response = await call_next(request)
        response.headers["X-Access-Token"] = access_token
        response.headers["X-Id-Token"] = id_token
        response.headers["X-User-Name"] = username
        response.headers["X-Email"] = email
        return response

# Global exception capture
biz_exception(app)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)


# changed from "/" to "/test" to avoid health check fails in ECS
@app.get("/test", status_code=status.HTTP_302_FOUND)
def index():
    return RedirectResponse("static/WebSocket.html")


# health check
@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/option", response_model=Option)
def option():
    return service.get_option()


@app.on_event("startup")
def set_history_in_share():
    logging.info("Setting history in share data")
    history_list = LogManagement.get_all_history()
    chat_history_session = {}
    for item in history_list:
        session_id = item['session_id']
        if session_id not in chat_history_session:
            chat_history_session[session_id] = []
        log_info = item['log_info']
        query = item['query']
        human_message = Message(type="human", content=query)
        bot_message = Message(type="AI", content=json.loads(log_info))
        chat_history_session[session_id].append(human_message)
        chat_history_session[session_id].append(bot_message)

    for key, value in chat_history_session.items():
        value = value[-MAX_CHAT_WINDOW_SIZE:]
        set_share_data(key, value)
    logging.info("Setting history in share data done")