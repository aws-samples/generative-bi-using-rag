from fastapi import status
from cryptography.hazmat.primitives import serialization
import jwt
import requests
import json
import os

from utils.logging import getLogger

JWKS_URL = os.getenv("OIDC_JWKS_URL")
AUDIENCE = os.getenv("OIDC_AUDIENCE")
if AUDIENCE:
    AUDIENCE = json.loads(AUDIENCE)
OPTIONS = os.getenv("OIDC_OPTIONS")
if OPTIONS:
    OPTIONS = json.loads(OPTIONS)

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
skipAuthentication = AWS_DEFAULT_REGION.startswith("cn")

logger = getLogger()

def jwt_decode(token):
    header = jwt.get_unverified_header(token)
    alg = header['alg']
    kid = header['kid']

    keys = requests.get(JWKS_URL).json()['keys']
    public_key = None
    for key in keys:
        if key['kid'] == kid:
            public_key = key

    rsa_pem_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(public_key))
    rsa_pem_key_bytes = rsa_pem_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return jwt.decode(
        token,
        key=rsa_pem_key_bytes,
        algorithms=[alg],
        verify=True,
        audience=AUDIENCE,
        options=OPTIONS
    )

def authenticate(access_token):
    logger.info("access-token:", access_token)

    if access_token and access_token.startswith("Bearer "):
        access_token = access_token[len("Bearer "):]

    if access_token is None:
        response = {}
        response['x-status-code'] = status.HTTP_401_UNAUTHORIZED
        return response

    if len(access_token.strip()) < 2:
        response = {}
        response['x-status-code'] = status.HTTP_401_UNAUTHORIZED
        return response

    if not access_token:
        print('Token: one of token is none')
        response = {}
        response['x-status-code'] = status.HTTP_401_UNAUTHORIZED
        return response
    try:
        jwt_decode(access_token)

    except Exception as e:
        logger.error('Token decode exception: ', str(e))
        response = {}
        response['x-status-code'] = status.HTTP_401_UNAUTHORIZED
        return response

    response = {}
    response['x-status-code'] = status.HTTP_200_OK

    return response
