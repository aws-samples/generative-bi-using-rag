from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from api.exception_handler import biz_exception
from api.main import router

app = FastAPI(title='GenBI')

# Global exception capture
biz_exception(app)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)

@app.get("/", status_code=status.HTTP_302_FOUND)
def index():
    return RedirectResponse("static/WebSocket.html")