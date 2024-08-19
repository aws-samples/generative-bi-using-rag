
from fastapi import FastAPI, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response
from api.exception_handler import biz_exception
from api.main import router
from fastapi.middleware.cors import CORSMiddleware
from api import service
from api.schemas import Option
from utils.auth import authenticate, skipAuthentication

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
    # print('---HTTP REQUEST---', vars(request), request.headers)

    if request.url.path == "/":
        return await call_next(request)

    if request.method == "OPTIONS":
        response = Response(status_code=status.HTTP_200_OK)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    if not skipAuthentication:
        access_token = request.headers.get("X-Access-Token")
        id_token = request.headers.get("X-Id-Token")
        refresh_token = request.headers.get("X-Refresh-Token")

        response = authenticate(access_token, id_token, refresh_token)
    else:
        response = {'X-Status-Code': status.HTTP_200_OK}

    if not skipAuthentication and response["X-Status-Code"] != status.HTTP_200_OK:

        response_error = Response(status_code=response["X-Status-Code"])
        response_error.headers["Access-Control-Allow-Origin"] = "*"
        response_error.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response_error.headers["Access-Control-Allow-Headers"] = "*"
        return response_error
    else:
        if not skipAuthentication:
            username = response["X-User-Name"]
        else:
            username = "admin"
        response = await call_next(request)
        if not skipAuthentication:
            response.headers["X-User-Name"] = username
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
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
