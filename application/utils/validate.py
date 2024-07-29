# -*- coding:utf-8 -*-
# @FileName  : validate.py
# @Time      : 2024/7/19 15:06
# @Author    : dingtianlu
# @Function  :
import json
from retrying import retry
import requests
import os
from utils.globals import g
from fastapi import HTTPException


@retry(stop_max_attempt_number=3, wait_fixed=1000)
def validate_token(token):
    validate_url = f"{os.getenv('VALIDATE_HOST')}/dops-temp/token/validate"
    response = requests.post(validate_url, data=token)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="validate token failed")
    else:
        payload = json.loads(response.text)
        if payload['data']:
            msg = json.loads(payload['msg'])
            g.user = msg
            return {
                "success": True,
                "user_id": msg['userId'],
                "user_name": msg['userName'],
            }
        else:
            return {
                "success": False,
                "msg": "Invalid token"
            }


def get_current_user(dlunifiedtoken: str):
    if dlunifiedtoken is None:
        raise HTTPException(status_code=403, detail="Cookie token missing")
    res = validate_token(dlunifiedtoken)
    if not res['success']:
        raise HTTPException(status_code=401, detail="Invalid token")
