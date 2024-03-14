import boto3
from loguru import logger
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


# DynamoDB table name
PROFILE_CONFIG_TABLE_NAME = 'NlqProfileConfig'


class ProfileConfigEntity:

    def __init__(self, profile_name: str, conn_name: str, schemas: list[str], tables: list[str], comments: str, tables_info: dict=None):
        self.profile_name = profile_name
        self.conn_name = conn_name
        self.schemas = schemas
        self.tables = tables
        self.comments = comments
        self.tables_info = tables_info

    def to_dict(self):
        """Convert to DynamoDB item format"""
        base_props = {
            'conn_name': self.conn_name,
            'profile_name': self.profile_name,
            'schemas': self.schemas,
            'tables': self.tables,
            'comments': self.comments
        }
        if self.tables_info:
            base_props['tables_info'] = self.tables_info
        return base_props


class ProfileConfigDao:

    def __init__(self, table_name_prefix=''):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = table_name_prefix + PROFILE_CONFIG_TABLE_NAME
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
                    {"AttributeName": "profile_name", "KeyType": "HASH"},  # Partition key
                    # {"AttributeName": "title", "KeyType": "RANGE"},  # Sort key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "profile_name", "AttributeType": "S"},
                    # {"AttributeName": "conn_name", "AttributeType": "S"},
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

    def get_by_name(self, profile_name):
        response = self.table.get_item(Key={'profile_name': profile_name})
        if 'Item' in response:
            return ProfileConfigEntity(**response['Item'])

    def add(self, entity):
        self.table.put_item(Item=entity.to_dict())

    def update(self, entity):
        self.table.put_item(Item=entity.to_dict())

    def delete(self, profile_name):
        self.table.delete_item(Key={'profile_name': profile_name})
        return True

    def get_profile_list(self):
        response = self.table.scan()
        return [ProfileConfigEntity(**item) for item in response['Items']]

    def update_table_def(self, profile_name, tables_info):
        try:
            response = self.table.update_item(
                Key={"profile_name": profile_name},
                UpdateExpression="set tables_info=:info",
                ExpressionAttributeValues={":info": tables_info},
                ReturnValues="UPDATED_NEW",
            )
        except ClientError as err:
            logger.error(
                "Couldn't update profile %s in table %s. Here's why: %s: %s",
                profile_name,
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return response["Attributes"]