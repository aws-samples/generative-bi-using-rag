import json
import logging

from fastapi import FastAPI, status, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response
from api.exception_handler import biz_exception
from api.main import router
from api.chart import router as dlset_router
from fastapi.middleware.cors import CORSMiddleware
from api import service
from api.schemas import Option, Message
import json
import base64

from nlq.business.log_store import LogManagement
from utils.tool import set_share_data, get_share_data
from utils.validate import validate_token

MAX_CHAT_WINDOW_SIZE = 10 * 2
app = FastAPI(title='GenBI')

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # 允许所有源访问，可以根据需求进行修改
    allow_credentials=True,  # 允许发送凭据（如Cookie）
    allow_methods=['*'],  # 允许所有HTTP方法
    allow_headers=['*'],  # 允许所有请求头
)

EXEMPT_PATHS = ["/info"]


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # 检查请求路径是否在免拦截列表中
    if request.url.path in EXEMPT_PATHS:
        return await call_next(request)
    print('---HTTP REQUEST---', vars(request), request.cookies)
    jwt_token = request.cookies.get('dlunifiedtoken', None)
    print('---JWT TOKEN---', jwt_token)
    if jwt_token:
        res = validate_token(jwt_token)
        if not res["success"]:
            return Response(status_code=status.HTTP_401_UNAUTHORIZED)
        else:
            response = await call_next(request)
            response.headers["X-User-Id"] = base64.b64encode(res['user_id'].encode('utf-8')).decode('utf-8')
            response.headers["X-User-Name"] = base64.b64encode(res['user_name'].encode('utf-8')).decode('utf-8')
            return response
    else:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

# Global exception capture
biz_exception(app)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)
app.include_router(dlset_router)

# changed from "/" to "/test" to avoid health check fails in ECS
@app.get("/test", status_code=status.HTTP_302_FOUND)
def index():
    return RedirectResponse("static/WebSocket.html")

# health check
@app.get("/info")
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