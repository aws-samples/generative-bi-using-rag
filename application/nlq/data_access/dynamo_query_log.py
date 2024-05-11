import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# DynamoDB table name
QUERY_LOG_TABLE_NAME = 'NlqQueryLogging'
DYNAMODB_AWS_REGION = os.environ.get('DYNAMODB_AWS_REGION')


class DynamoQueryLogEntity:
    def __init__(self, log_id, profile_name, sql, query, intent, log_info, time_str):
        self.log_id = log_id
        self.profile_name = profile_name
        self.sql = sql
        self.query = query
        self.intent = intent
        self.log_info = log_info
        self.time_str = time_str

    def to_dict(self):
        """Convert to DynamoDB item format"""
        return {
            'log_id': self.log_id,
            'profile_name': self.profile_name,
            'sql': self.sql,
            'query': self.query,
            'intent': self.intent,
            'log_info': self.log_info,
            'time_str': self.time_str
        }


class DynamoQueryLogDao:

    def __init__(self, table_name_prefix=''):
        self.dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_AWS_REGION)
        self.table_name = table_name_prefix + QUERY_LOG_TABLE_NAME
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
                    {"AttributeName": "log_id", "KeyType": "HASH"},  # Partition key
                    # {"AttributeName": "title", "KeyType": "RANGE"},  # Sort key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "log_id", "AttributeType": "S"},
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

    def add(self, entity):
        try:
            self.table.put_item(Item=entity.to_dict())
        except Exception as e:
            logger.error("add log entity is error {}",e)

    def update(self, entity):
        self.table.put_item(Item=entity.to_dict())

    def add_log(self, log_id, profile_name, sql, query, intent, log_info, time_str):
        entity = DynamoQueryLogEntity(log_id, profile_name, sql, query, intent, log_info, time_str)
        self.add(entity)
