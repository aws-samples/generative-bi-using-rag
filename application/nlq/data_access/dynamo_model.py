import os

import boto3
import logging
from typing import List
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from utils.prompts.generate_prompt import prompt_map_dict

logger = logging.getLogger(__name__)

# DynamoDB table name
MODEL_CONFIG_TABLE_NAME = 'NlqModelConfig'
DYNAMODB_AWS_REGION = os.environ.get('DYNAMODB_AWS_REGION')

class ModelConfigEntity:

    def __init__(self, model_id: str, model_region: str, prompt_template: str,
                 input_payload: str, output_format: str):
        self.model_id = model_id
        self.model_region = model_region
        self.prompt_template = prompt_template
        self.input_payload = input_payload
        self.output_format = output_format


    def to_dict(self):
        """Convert to DynamoDB item format"""
        base_props = {
            'model_id': self.model_id,
            'model_region': self.model_region,
            'prompt_template': self.prompt_template,
            'input_payload': self.input_payload,
            'output_format': self.output_format
        }
        return base_props


class ModelConfigDao:

    def __init__(self, table_name_prefix=''):
        self.dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_AWS_REGION)
        self.table_name = table_name_prefix + MODEL_CONFIG_TABLE_NAME
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
                    {"AttributeName": "model_id", "KeyType": "HASH"},  # Partition key
                    # {"AttributeName": "title", "KeyType": "RANGE"},  # Sort key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "model_id", "AttributeType": "S"},
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

    def get_by_id(self, model_id):
        response = self.table.get_item(Key={'model_id': model_id})
        if 'Item' in response:
            return ModelConfigEntity(**response['Item'])

    def add(self, entity):
        self.table.put_item(Item=entity.to_dict())

    def update(self, entity):
        self.table.put_item(Item=entity.to_dict())

    def delete(self, model_id):
        self.table.delete_item(Key={'model_id': model_id})
        return True

    def get_model_list(self):
        response = self.table.scan()
        return [ModelConfigEntity(**item) for item in response['Items']]

