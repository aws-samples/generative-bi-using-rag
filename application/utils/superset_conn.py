import datetime
import json
import os
import jwt
import requests
from retrying import retry
from nlq.business.connection import ConnectionManagement
from utils.globals import g


def create_admin_token():
    sso_jwt_algorithm = "HS512"
    sso_jwt_headers = {
        'typ': 'jwt',
        'alg': sso_jwt_algorithm
    }
    payload = {"user_id": "admin", "user_name": "admin",
               "email": "admin@admin.com",
               "exp": datetime.datetime.now() + datetime.timedelta(days=1), "source": 0}
    result = jwt.encode(payload=payload, key=os.getenv('SSO_JWT_SECRET_KEY'), algorithm=sso_jwt_algorithm,
                        headers=sso_jwt_headers)
    return result


@retry(stop_max_attempt_number=3, wait_fixed=1000)
def get_superset_conn():
    token = create_admin_token()
    headers = {
        'Cookie': f'dlunifiedtoken={token}'
    }
    payload = {}
    url = f"{os.getenv('SUPERSET_HOST')}/api/v1/database/list"
    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to get Superset connection")


def import_superset_conn(db_types: list):
    db_conn_names = ConnectionManagement.get_all_connections()
    superset_conns = get_superset_conn()
    for conn in superset_conns['result']:
        if conn['db_type'] in db_types:
            if conn['database_name'] not in db_conn_names:
                ConnectionManagement.add_connection(conn['database_id'],
                                                    conn['database_name'],
                                                    conn['db_type'],
                                                    conn['config']['host'],
                                                    conn['config']['port'],
                                                    conn['config']['username'],
                                                    conn['config']['password'],
                                                    conn['config']['database'],
                                                    None)


@retry(stop_max_attempt_number=3, wait_fixed=1000)
def get_superset_rlf(table_name: str, schema: str, database_id: int):
    payload = json.dumps({
        "table_name": table_name,
        "schema": schema,
        "database_id": database_id
    })
    headers = {
        'Cookie': f"dlunifiedtoken={g.user['jwtToken']}",
        'Content-Type': 'application/json'
    }
    resp = requests.request("POST", os.getenv('SUPERSET_HOST') + '/api/v1/dataset/rlf', headers=headers, data=payload)
    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception("Failed to get Superset RLF")