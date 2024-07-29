from fastapi import FastAPI, status, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response
from api.exception_handler import biz_exception
from api.main import router
from api.chart import router as dlset_router
from fastapi.middleware.cors import CORSMiddleware
from api import service
from api.schemas import Option
import json
import base64

from utils.validate import validate_token

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
