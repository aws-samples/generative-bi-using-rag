from fastapi import status, Request
from fastapi.responses import Response
from jose import jwt
import requests
import os

REGION = os.getenv("COGNITO_REGION")
USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")
AUTH_PATH = os.getenv("COGNITO_AUTH_PATH")
USER_ROLES_CLAIM = os.getenv("USER_ROLES_CLAIM", "cognito:groups")

JWKS_URL = os.getenv("JWKS_URL",
                        f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/" ".well-known/jwks.json")

TOKEN_URL = f"{AUTH_PATH}/oauth2/token"

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
    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)

    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": 'refresh_token', "refresh_token": refresh_token, "client_id": CLIENT_ID},
        auth=auth,
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
    print('---ACCESS TOKEN---', access_token)
    print('---ID TOKEN---', id_token)
    print('---REFRESH TOKEN---', refresh_token)

    if not access_token or not id_token or not refresh_token:
        response = {}
        response['X-Status-Code'] = status.HTTP_401_UNAUTHORIZED
        return response
    try:
        decoded = jwt_decode(access_token)

    except jwt.ExpiredSignatureError:
        tokens = refresh_tokens(refresh_token)
        access_token = tokens['accessToken']
        id_token = tokens['idToken']

        decoded = jwt_decode(access_token)

    except Exception as e:
        response = {}
        response['X-Status-Code'] = status.HTTP_401_UNAUTHORIZED
        return response

    response = {}
    response['X-Status-Code'] = status.HTTP_200_OK
    response["X-Access-Token"] = access_token
    response["X-ID-Token"] = id_token

    claims = ["email"]
    identity = get_cognito_identity_from_token(decoded=decoded, claims=claims)

    if id_token:
        decoded_id = jwt_decode(id_token, audience=CLIENT_ID, access_token=access_token)
        identity_from_id_token = get_cognito_identity_from_token(decoded=decoded_id, claims=claims)
        identity.update(identity_from_id_token)

    response["X-User-Name"] = identity["username"]
    response["X-Email"] = identity["attributes"]["email"]
    return response
