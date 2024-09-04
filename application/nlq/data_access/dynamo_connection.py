import os
import boto3
import logging
import random
import string
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import json

load_dotenv()

logger = logging.getLogger(__name__)

# DynamoDB 表名
CONNECT_CONFIG_TABLE_NAME = 'NlqConnectConfig'
DYNAMODB_AWS_REGION = os.environ.get('DYNAMODB_AWS_REGION')


class ConnectConfigEntity:
    """Connect config entity mapped to DynamoDB item"""

    def __init__(self, conn_name, db_type, db_name, db_host, db_port, db_user, db_pwd,comment, db_sm=None, id=None):
        self.id = id
        self.conn_name = conn_name
        self.db_type = db_type
        self.db_name = db_name
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_pwd = db_pwd
        self.db_sm = db_sm
        self.comment = comment

    def to_dict(self):
        """Convert to DynamoDB item format"""
        return {
            'id': self.id,
            'conn_name': self.conn_name,
            'db_type': self.db_type,
            'db_name': self.db_name,
            'db_host': self.db_host,
            'db_port': self.db_port,
            'db_user': self.db_user,
            'db_pwd': self.db_pwd,
            'db_sm': self.db_sm,
            'comment': self.comment
        }

    def get_secrets_manager_name(self):
        """Generate a random Secrets Manager name"""
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return f"GenBI-{self.conn_name}-{random_str}"


class ConnectConfigDao:
    def __init__(self, table_name_prefix=''):
        self.dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_AWS_REGION)
        self.secrets_manager = boto3.client('secretsmanager', region_name=DYNAMODB_AWS_REGION)
        self.table_name = table_name_prefix + CONNECT_CONFIG_TABLE_NAME

        if self.exists():
            self.table = self.dynamodb.Table(self.table_name)
            self.check_and_update_table()
        else:
            self.create_table()
            self.table = self.dynamodb.Table(self.table_name)

    def check_and_update_table(self):
        try:
            # 获取表的描述
            table_description = self.dynamodb.meta.client.describe_table(TableName=self.table_name)

            if 'Table' in table_description:
                attribute_definitions = table_description['Table']['AttributeDefinitions']
                logger.info(f"Attribute Definitions: {attribute_definitions}")
            else:
                logger.error("Table description does not contain 'Table' key.")
        except ClientError as err:
            logger.error(f"Couldn't describe table {self.table_name}. Here's why: {err.response['Error']['Message']}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")

    def exists(self):
        """Determines whether a table exists."""
        try:
            table = self.dynamodb.Table(self.table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                exists = False
                logger.info("Table does not exist")
            else:
                logger.error(
                    "Couldn't check for existence of %s. Here's why: %s: %s",
                    self.table_name,
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise
        return exists

    def create_table(self):
        try:
            self.table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {"AttributeName": "conn_name", "KeyType": "HASH"},  # Partition key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "conn_name", "AttributeType": "S"},
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 2,
                    "WriteCapacityUnits": 1,
                },
            )
            self.table.wait_until_exists()
            logger.info(f"DynamoDB Table {self.table_name} created")
        except ClientError as err:
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s",
                self.table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def get_by_name(self, conn_name):
        response = self.table.get_item(Key={'conn_name': conn_name})

        if 'Item' in response:
            item = response['Item']
            db_sm = item.get('db_sm', None)  # 获取 db_sm 值,如果不存在则为 None

            # 先判断 db_sm 是否存在
            if db_sm:
                # 如果 db_sm 存在,则从 Secrets Manager 中获取 db_host、db_port、db_user、db_pwd
                secrets_manager_name = db_sm
                secrets_response = self.secrets_manager.get_secret_value(SecretId=secrets_manager_name)
                if 'SecretString' in secrets_response:
                    secrets = json.loads(secrets_response['SecretString'])
                    db_host = secrets['db_host']
                    db_port = secrets['db_port']
                    db_user = secrets['db_user']
                    db_pwd = secrets['db_pwd']
            else:
                # 如果 db_sm 不存在,则从 DynamoDB 中获取 db_host、db_port、db_user、db_pwd
                db_host = item.get('db_host', '')
                db_port = item.get('db_port', 0)
                db_user = item.get('db_user', '')
                db_pwd = item.get('db_pwd', '')

            # 创建 ConnectConfigEntity 实例
            return ConnectConfigEntity(
                id=item.get('id', None),
                conn_name=item['conn_name'],
                db_type=item.get('db_type', ''),
                db_name=item.get('db_name', ''),
                db_host=db_host,
                db_port=db_port,
                db_user=db_user,
                db_pwd=db_pwd,
                db_sm=db_sm,
                comment=item.get('comment', '')
            )

    def add(self, entity):
        # 检查 conn_name 是否已存在
        existing_entity = self.get_by_name(entity.conn_name)
        if existing_entity:
            raise ValueError(
                f"Database connection name '{entity.conn_name}' already exists in DynamoDB! Please try another name.")

        # 将 db_host、db_port、db_user、db_pwd 存储在 Secrets Manager 中
        secrets_manager_name = entity.get_secrets_manager_name()
        secrets = {
            'db_host': entity.db_host,
            'db_port': str(entity.db_port),
            'db_user': entity.db_user,
            'db_pwd': entity.db_pwd
        }
        self.secrets_manager.create_secret(
            Name=secrets_manager_name,
            SecretString=json.dumps(secrets)
        )

        # 在 DynamoDB 中存储其他数据和 Secrets Manager 名称
        entity.db_host = ''
        entity.db_port = 0
        entity.db_user = ''
        entity.db_pwd = ''
        entity.db_sm = secrets_manager_name
        self.table.put_item(Item=entity.to_dict())

    def update(self, entity):
        # 如果修改了 db_host、db_port、db_user、db_pwd 中的任何一个
        if entity.db_sm:
            secrets_manager_name = entity.db_sm
            logger.info(f"Updating secrets for: {secrets_manager_name}")

            secrets = {
                'db_host': entity.db_host,
                'db_port': str(entity.db_port),
                'db_user': entity.db_user,
                'db_pwd': entity.db_pwd
            }

            try:
                self.secrets_manager.put_secret_value(
                    SecretId=secrets_manager_name,
                    SecretString=json.dumps(secrets)
                )
            except self.secrets_manager.exceptions.ResourceNotFoundException as e:
                logger.error(f"Secrets Manager key not found: {secrets_manager_name}")
                logger.error(f"Error details: {str(e)}")
                raise Exception(f"Failed to update Secrets Manager key: {secrets_manager_name}")
            # 创建一个新的字典,只包含需要保存到 DynamoDB 的字段
            dynamodb_item = {
                'conn_name': entity.conn_name,
                'db_type': entity.db_type,
                'db_name': entity.db_name,
                'db_sm': entity.db_sm,
                'comment': entity.comment,
                'db_host': '',
                'db_port': '',
                'db_user': '',
                'db_pwd': ''
            }
        else:
            # 如果 entity.db_sm 为空值,则将所有字段都存储到 DynamoDB 中
            dynamodb_item = {
                'conn_name': entity.conn_name,
                'db_type': entity.db_type,
                'db_name': entity.db_name,
                'db_sm': entity.db_sm,
                'comment': entity.comment,
                'db_host': entity.db_host,
                'db_port': str(entity.db_port),
                'db_user': entity.db_user,
                'db_pwd': entity.db_pwd
            }

        # 将新字典保存到 DynamoDB 表中
        self.table.put_item(Item=dynamodb_item)

    def delete(self, conn_name):
        entity = self.get_by_name(conn_name)
        if entity.db_sm:
            # 删除 Secrets Manager 中的数据
            self.secrets_manager.delete_secret(SecretId=entity.db_sm)
        # 删除 DynamoDB 中的数据
        self.table.delete_item(Key={'conn_name': conn_name})
        return True

    def add_url_db(self, conn_name, db_type, db_host, db_port, db_user, db_pwd, db_name, db_sm, comment=""):
        entity = ConnectConfigEntity(conn_name, db_type, db_name, db_host, db_port, db_user, db_pwd, db_sm, comment)
        self.add(entity)

    def update_db_info(self, conn_name, db_type=None, db_host=None, db_port=None, db_user=None, db_pwd=None,
                       db_name=None, db_sm=None, comment=None):
        entity = self.get_by_name(conn_name)
        if entity:
            if db_type is not None:
                entity.db_type = db_type
            if db_host is not None:
                entity.db_host = db_host
            if db_port is not None:
                entity.db_port = db_port
            if db_user is not None:
                entity.db_user = db_user
            if db_pwd is not None:
                entity.db_pwd = db_pwd
            if db_name is not None:
                entity.db_name = db_name
            # if db_sm is not None:
            #     entity.db_sm = db_sm
            if comment is not None:
                entity.comment = comment

            self.update(entity)
            return True
        else:
            raise ValueError(f"{conn_name} not found")

    def get_db_list(self):
        response = self.table.scan()
        db_list = []
        # item['id'] = None
        for item in response['Items']:
            if "db_sm" not in item:
                db_sm = None
            else:
                db_sm = item['db_sm']
            if db_sm:
                # 从 Secrets Manager 中获取 db_host、db_port、db_user、db_pwd
                secrets_manager_name = db_sm
                secrets_response = self.secrets_manager.get_secret_value(SecretId=secrets_manager_name)
                if 'SecretString' in secrets_response:
                    secrets = json.loads(secrets_response['SecretString'])
                    item['db_host'] = secrets['db_host']
                    item['db_port'] = secrets['db_port']
                    item['db_user'] = secrets['db_user']
                    item['db_pwd'] = secrets['db_pwd']
            db_list.append(ConnectConfigEntity(**item))
        return db_list