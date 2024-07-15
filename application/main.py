from fastapi import FastAPI, status, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response
from api.exception_handler import biz_exception
from api.main import router
from fastapi.middleware.cors import CORSMiddleware
from api import service
from api.schemas import Option
import requests
import json
import base64

app = FastAPI(title='GenBI')

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # 允许所有源访问，可以根据需求进行修改
    allow_credentials=True,  # 允许发送凭据（如Cookie）
    allow_methods=['*'],  # 允许所有HTTP方法
    allow_headers=['*'],  # 允许所有请求头
)

validate_url = 'https://apimarket-test.shinho.net.cn/dops-temp/token/validate'

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    print('---HTTP REQUEST---', vars(request), request.cookies)
    jwt_token = request.cookies.get('jwtToken', None)
    print('---JWT TOKEN---', jwt_token)
    if jwt_token:
        response = requests.post(validate_url, data=jwt_token)
        if response.status_code != 200 :
            return Response(status_code=status.HTTP_401_UNAUTHORIZED)
        else:
            payload = json.loads(response.text)
            if payload['data']:
                msg = json.loads(payload['msg'])
                response = await call_next(request)
                response.headers["X-User-Id"] = base64.b64encode(msg['userId'].encode('utf-8')).decode('utf-8')
                response.headers["X-User-Name"] = base64.b64encode(msg['userName'].encode('utf-8')).decode('utf-8')
                return response
            else:
                return Response(status_code=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

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
