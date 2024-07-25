# -*- coding:utf-8 -*-
# @FileName  : validate.py
# @Time      : 2024/7/19 15:06
# @Author    : dingtianlu
# @Function  :
from typing import Optional

import requests
import os

from fastapi import HTTPException
from fastapi.responses import Response


def validate_token(token):
    validate_url = f"{os.getenv('VALIDATE_HOST')}/dops-temp/token/validate"
    response = requests.post(validate_url, data=token)
    return response


def get_current_user(dlunifiedtoken: str):
    if dlunifiedtoken is None:
        raise HTTPException(status_code=403, detail="Cookie token missing")
    response = validate_token(dlunifiedtoken)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="validate token failed")
    else:
        payload = response.json()
        if not payload['data']:
            raise HTTPException(status_code=401, detail="Invalid token")
