import logging

from fastapi import status, Request
from fastapi.responses import Response
from jose import jwt
import requests
import os

VITE_COGNITO_REGION = os.getenv("VITE_COGNITO_REGION")
USER_POOL_ID = os.getenv("VITE_COGNITO_USER_POOL_ID")
CLIENT_ID = os.getenv("VITE_COGNITO_USER_POOL_WEB_CLIENT_ID")
AUTH_PATH = os.getenv("COGNITO_AUTH_PATH")
USER_ROLES_CLAIM = os.getenv("USER_ROLES_CLAIM", "cognito:groups")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
skipAuthentication = AWS_DEFAULT_REGION.startswith("cn")

JWKS_URL = os.getenv("JWKS_URL",
                        f"https://cognito-idp.{VITE_COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}/" ".well-known/jwks.json")

TOKEN_URL = f"{AUTH_PATH}/oauth2/token"

logger = logging.getLogger(__name__)

def jwt_decode(token, audience=None, access_token=None):
    return jwt.decode(
            token, requests.get(JWKS_URL).json(), audience=audience, access_token=access_token, algorithms=["RS256"]
        )

class RefreshTokenError(Exception):
    ERROR_FMT = 'Refresh token error: {description}'
    description = 'Refresh token flow failed'

    def __init__(self, description=None):
        if description:
            self.description = self.ERROR_FMT.format(description=description)

    def __str__(self):
        return self.description

def refresh_tokens(refresh_token):

    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": 'refresh_token', "refresh_token": refresh_token, "client_id": CLIENT_ID},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if resp.status_code != 200:
        raise RefreshTokenError(resp.json().get('error'))

    values = resp.json()
    access_token = values.get("access_token")
    id_token = values.get("id_token")

    return {'accessToken': access_token, 'idToken': id_token}

def get_cognito_identity_from_token(decoded, claims):
    identity = {"attributes": {}}

    if USER_ROLES_CLAIM in decoded:
        identity["user_roles"] = decoded[USER_ROLES_CLAIM]
    if "username" in decoded:
        identity["username"] = decoded["username"]

    for claim in claims:
        if claim in decoded:
            identity["attributes"][claim] = decoded[claim]

    return identity

def authenticate(access_token, id_token, refresh_token):
    if access_token and access_token.startswith("Bearer "):
        access_token = access_token[len("Bearer "):]

    if id_token and id_token.startswith("Bearer "):
        id_token = id_token[len("Bearer "):]

    if refresh_token and refresh_token.startswith("Bearer "):
        refresh_token = refresh_token[len("Bearer "):]

    if access_token is None or id_token is None or refresh_token is None:
        response = {}
        response['X-Status-Code'] = status.HTTP_401_UNAUTHORIZED
        return response

    if len(access_token.strip()) < 2 or len(id_token.strip()) < 2 or len(refresh_token.strip()) < 2:
        response = {}
        response['X-Status-Code'] = status.HTTP_401_UNAUTHORIZED
        return response

    # print('---ACCESS TOKEN---', access_token)
    # print('---ID TOKEN---', id_token)
    # print('---REFRESH TOKEN---', refresh_token)

    if not access_token or not id_token or not refresh_token:
        print('Token: one of token is none')
        response = {}
        response['X-Status-Code'] = status.HTTP_401_UNAUTHORIZED
        return response
    try:
        decoded = jwt_decode(access_token)
        # print('Token decoded:', decoded)

    except Exception as e:
        logger.error('Token decode exception: ', str(e))
        response = {}
        response['X-Status-Code'] = status.HTTP_401_UNAUTHORIZED
        return response

    response = {}
    response['X-Status-Code'] = status.HTTP_200_OK

    claims = ["email"]
    identity = get_cognito_identity_from_token(decoded=decoded, claims=claims)

    print("Identity:", identity)

    if id_token:
        decoded_id = jwt_decode(id_token, audience=CLIENT_ID, access_token=access_token)
        identity_from_id_token = get_cognito_identity_from_token(decoded=decoded_id, claims=claims)
        identity.update(identity_from_id_token)

    response["X-User-Name"] = identity["username"]
    #response["X-Email"] = identity["attributes"]["email"]
    return response
