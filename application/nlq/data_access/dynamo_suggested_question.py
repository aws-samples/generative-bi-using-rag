from datetime import datetime, timezone
from application.utils.prompt import SUGGESTED_QUESTION_PROMPT_CLAUDE3
import boto3
from loguru import logger
from botocore.exceptions import ClientError
from utils.constant import PROFILE_QUESTION_TABLE_NAME, ACTIVE_PROMPT_NAME, DEFAULT_PROMPT_NAME

class SuggestedQuestionEntity:

    def __init__(self, prompt: str, create_time: str, prompt_name: str = ACTIVE_PROMPT_NAME):
        self.prompt_name = prompt_name
        self.prompt = prompt
        self.create_time = create_time

    def to_dict(self):
        """Convert to DynamoDB item format"""
        base_props = {
            'prompt_name': self.prompt_name,
            'prompt': self.prompt,
            'create_time': self.create_time
        }
        return base_props

class SuggestedQuestionDao:

    def __init__(self, table_name_prefix=''):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = table_name_prefix + PROFILE_QUESTION_TABLE_NAME
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

        return exists

    def create_table(self):
        try:
            self.table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {"AttributeName": "prompt_name", "KeyType": "HASH"},  # Partition key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "prompt_name", "AttributeType": "S"},
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 2,
                    "WriteCapacityUnits": 1,
                },
            )
            self.table.wait_until_exists()
            
            # Add default prompt
            current_time = datetime.now(timezone.utc)
            formatted_time = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            item = {
                "prompt_name": {"S": DEFAULT_PROMPT_NAME},
                "prompt": {"S": SUGGESTED_QUESTION_PROMPT_CLAUDE3},
                "create_time": {"S": formatted_time},
            }
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=item,
            )

            # Add active prompt
            current_time = datetime.now(timezone.utc)
            formatted_time = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            item = {
                "prompt_name": {"S": ACTIVE_PROMPT_NAME},
                "prompt": {"S": SUGGESTED_QUESTION_PROMPT_CLAUDE3},
                "create_time": {"S": formatted_time},
            }
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=item,
            )
            logger.info(f"Item added successfully to table %s.", self.table_name)
        except ClientError as err:
            logger.error(type(err))
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s",
                self.table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def get_by_name(self, prompt_name):
        response = self.table.get_item(Key={'prompt_name': prompt_name})
        if 'Item' in response:
            return SuggestedQuestionEntity(**response['Item'])

    def update(self, entity):
        self.table.put_item(Item=entity.to_dict())

    def get_profile_list(self):
        response = self.table.scan()
        return [SuggestedQuestionEntity(**item) for item in response['Items']]

    def update_prompt(self, prompt: str, create_time: str, prompt_name: str = ACTIVE_PROMPT_NAME):
        """Update prompt template in DynamoDB table

        Args:
            prompt_name (str): prompt item name
            prompt (str): prompt content
            create_time (str): creation time
        """
        try:
            response = self.table.update_item(
                Key={"prompt_name": {"S": prompt_name}},
                UpdateExpression="SET prompt = :prompt, create_time = :create_time",
                ExpressionAttributeValues={
                    ":prompt": {"S": prompt},
                    ":create_time": {"S": create_time},
                }
            )
        except ClientError as err:
            logger.error(
                "Couldn't update profile %s in table %s. Here's why: %s: %s",
                prompt_name,
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return response["Attributes"]
