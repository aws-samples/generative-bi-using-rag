import os
from fastapi.responses import JSONResponse
from fastapi import status, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from .enum import ErrorEnum
import traceback
import logging
logger = logging.getLogger(__name__)

def response_error(code: int, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
    headers = {}
    return JSONResponse(
        content={
            'code': code,
            'message': message,
        },
        headers=headers,
        status_code=status_code,
    )


def biz_exception(app: FastAPI):
    # customize request validation error
    @app.exception_handler(RequestValidationError)
    async def val_exception_handler(req: Request, rve: RequestValidationError, code: int = status.HTTP_422_UNPROCESSABLE_ENTITY):
        lst = []
        for error in rve.errors():
            lst.append('{}=>{}'.format('.'.join(error['loc']), error['msg']))
        return response_error(code, ' , '.join(lst))

    # customize business error
    @app.exception_handler(BizException)
    async def biz_exception_handler(req: Request, exc: BizException):
        return response_error(exc.code, exc.message)

    # system error
    @app.exception_handler(Exception)
    async def exception_handler(req: Request, exc: Exception):
        if isinstance(exc, BizException):
            return
        error_msg = traceback.format_exc()
        logger.error(error_msg)
        return response_error(ErrorEnum.UNKNOWN_ERROR.get_code(), error_msg, status.HTTP_500_INTERNAL_SERVER_ERROR)


class BizException(Exception):
    def __init__(self, error_message: ErrorEnum):
        self.code = error_message.get_code()
        self.message = error_message.get_message()


    def __msg__(self):
        return self.message
