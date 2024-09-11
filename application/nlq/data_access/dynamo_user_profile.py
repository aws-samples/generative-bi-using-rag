import os

import boto3
import logging
from typing import List
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from utils.prompts.generate_prompt import prompt_map_dict

logger = logging.getLogger(__name__)

# DynamoDB table name
PROFILE_CONFIG_TABLE_NAME = 'NlqUserProfileConfig'
DYNAMODB_AWS_REGION = os.environ.get('DYNAMODB_AWS_REGION')

class UserProfileConfigEntity:

    def __init__(self, user_id: str, profile_name_list: List[str]):
        self.user_id = user_id
        self.profile_name_list = profile_name_list


    def to_dict(self):
        """Convert to DynamoDB item format"""
        base_props = {
            'user_id': self.user_id,
            'profile_name_list': self.profile_name_list
        }
        return base_props


class UserProfileConfigDao:

    def __init__(self, table_name_prefix=''):
        self.dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_AWS_REGION)
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
            self.table = table
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
                    {"AttributeName": "user_id", "KeyType": "HASH"},  # Partition key
                    # {"AttributeName": "title", "KeyType": "RANGE"},  # Sort key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "user_id", "AttributeType": "S"},
                    # {"AttributeName": "conn_name", "AttributeType": "S"},
                ],
                BillingMode='PAY_PER_REQUEST',
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

    def get_by_name(self, user_id):
        try:
            response = self.table.get_item(Key={'user_id': user_id})
            if 'Item' in response:
                return UserProfileConfigEntity(**response['Item'])
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
        except ClientErrError as err:
            print(type(err))
            logger.error(
                "Couldn't add record in table %s. Here's why: %s: %s",
                self.table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def update(self, entity):
        self.table.put_item(Item=entity.to_dict())

    def delete(self, user_id):
        self.table.delete_item(Key={'user_id': user_id})
        return True

    def get_user_profile_list(self):
        response = self.table.scan()
        print(response)
        return [UserProfileConfigEntity(**item) for item in response['Items']]

    def update_table_def(self, user_id, profile_name_list):
        try:
            response = self.table.update_item(
                Key={"user_id": user_id},
                UpdateExpression="set profile_name_list=:info",
                ExpressionAttributeValues={":info": profile_name_list},
                ReturnValues="UPDATED_NEW",
            )
        except ClientError as err:
            logger.error(
                "Couldn't update user_id %s in table %s. Here's why: %s: %s",
                user_id,
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return response["Attributes"]

