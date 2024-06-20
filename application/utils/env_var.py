import json
import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

RDS_MYSQL_USERNAME = os.getenv('RDS_MYSQL_USERNAME')
RDS_MYSQL_PASSWORD = os.getenv('RDS_MYSQL_PASSWORD')
RDS_MYSQL_HOST = os.getenv('RDS_MYSQL_HOST')
RDS_MYSQL_PORT = os.getenv('RDS_MYSQL_PORT')
RDS_MYSQL_DBNAME = os.getenv('RDS_MYSQL_DBNAME')

RDS_PQ_SCHEMA = os.getenv('RDS_PQ_SCHEMA')

BEDROCK_REGION = os.getenv('BEDROCK_REGION')

DYNAMODB_AWS_REGION = os.getenv('DYNAMODB_AWS_REGION')

AOS_HOST = os.getenv('AOS_HOST')
AOS_PORT = os.getenv('AOS_PORT')
AOS_USER = os.getenv('AOS_USER')
AOS_PASSWORD = os.getenv('AOS_PASSWORD')

AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')

OPENSEARCH_TYPE = os.getenv('OPENSEARCH_TYPE')


def get_opensearch_parameter():
    try:
        session = boto3.session.Session()
        sm_client = session.client(service_name='secretsmanager', region_name=AWS_DEFAULT_REGION)
        master_user = sm_client.get_secret_value(SecretId='opensearch-host-url')['SecretString']
        data = json.loads(master_user)
        es_host_name = data.get('host')
        # cluster endpoint, for example: my-test-domain.us-east-1.es.amazonaws.com/
        host = es_host_name + '/' if es_host_name[-1] != '/' else es_host_name
        host = host[8:-1]

        sm_client = session.client(service_name='secretsmanager', region_name=AWS_DEFAULT_REGION)
        master_user = sm_client.get_secret_value(SecretId='opensearch-master-user')['SecretString']
        data = json.loads(master_user)
        username = data.get('username')
        password = data.get('password')
        port = 443
        return host, port, username, password
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e


if OPENSEARCH_TYPE == "service":
    opensearch_host, opensearch_port, opensearch_username, opensearch_password = get_opensearch_parameter()
    AOS_HOST = opensearch_host
    AOS_PORT = opensearch_port
    AOS_USER = opensearch_username
    AOS_PASSWORD = opensearch_password
