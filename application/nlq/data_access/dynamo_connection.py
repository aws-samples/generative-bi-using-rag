import boto3
from loguru import logger
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


# DynamoDB table name
CONNECT_CONFIG_TABLE_NAME = 'NlqConnectConfig'


class ConnectConfigEntity:
    """Connect config entity mapped to DynamoDB item"""

    def __init__(self, id, conn_name, db_type, db_name, db_host, db_port, db_user, db_pwd, comment):
        self.id = id
        self.conn_name = conn_name
        self.db_type = db_type
        self.db_name = db_name
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_pwd = db_pwd
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
            'comment': self.comment
        }


class ConnectConfigDao:

    def __init__(self, table_name_prefix=''):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = table_name_prefix + CONNECT_CONFIG_TABLE_NAME
        if not self.exists():
            self.create_table()
        self.table = self.dynamodb.Table(self.table_name)

    def exists(self):
        """
        Determines whether a table exists. As a side effect, stores the table in
        a member variable.

        :param table_name: The name of the table to check.
        :return: True when the table exists; otherwise, False.
        """
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
        # else:
        #     self.table = table
        return exists

    def create_table(self):
        try:
            self.table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {"AttributeName": "conn_name", "KeyType": "HASH"},  # Partition key
                    # {"AttributeName": "title", "KeyType": "RANGE"},  # Sort key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "conn_name", "AttributeType": "S"},
                    # {"AttributeName": "title", "AttributeType": "S"},
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 2,
                    "WriteCapacityUnits": 1,
                },
            )
            self.table.wait_until_exists()
            logger.info(f"DynamoDB Table {self.table_name} created")
        except ClientError as err:
            print(type(err))
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
            return ConnectConfigEntity(**response['Item'])

    def add(self, entity):
        self.table.put_item(Item=entity.to_dict())

    def update(self, entity):
        self.table.put_item(Item=entity.to_dict())

    def delete(self, conn_name):
        self.table.delete_item(Key={'conn_name': conn_name})
        return True

    def get_by_names(self, conn_name):
        response = self.table.get_item(Key={'conn_name': conn_name})
        if 'Item' in response:
            return ConnectConfigEntity(**response['Item'])

    def add_url_db(self, conn_name, db_type, db_host, db_port, db_user, db_pwd, db_name, comment=""):
        entity = ConnectConfigEntity(None, conn_name, db_type, db_name, db_host, db_port, db_user, db_pwd, comment)
        self.add(entity)

    def update_db_info(self, conn_name, db_type, db_host="", db_port=0, db_user="", db_pwd="", db_name="", comment=""):
        entity = self.get_by_name(conn_name)
        if entity:
            entity.db_type = db_type
            entity.db_host = db_host
            entity.db_port = db_port
            entity.db_user = db_user
            entity.db_pwd = db_pwd
            entity.db_name = db_name
            entity.comment = comment
            self.update(entity)
            return True
        else:
            raise ValueError(f"{conn_name} not found")

    def get_db_list(self):
        response = self.table.scan()
        return [ConnectConfigEntity(**item) for item in response['Items']]
