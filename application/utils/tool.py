import json
import time
import random
import datetime

import pandas as pd

from utils.logging import getLogger

logger = getLogger()

def get_generated_sql(generated_sql_response):
    sql = ""
    try:
        if "<sql>" in generated_sql_response:
            return generated_sql_response.split("<sql>")[1].split("</sql>")[0]
        elif "```sql" in generated_sql_response:
            return generated_sql_response.split("```sql")[1].split("```")[0]
    except IndexError:
        logger.error("No SQL found in the LLM's response")
        logger.error(generated_sql_response)
    return sql


def generate_log_id():
    timestamp = int(time.time() * 1000000)
    random_part = random.randint(0, 9999)
    log_id = f"{timestamp}{random_part:04d}"
    return log_id


def get_current_time():
    now = datetime.datetime.now()
    formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time


def get_generated_sql_explain(generated_sql_response):
    try:
        if "<sql>" in generated_sql_response:
            return generated_sql_response.split("<sql>")[1].split("</sql>")[1]
        elif "```sql" in generated_sql_response:
            return generated_sql_response.split("```sql")[1].split("```")[1]
        else:
            return generated_sql_response
    except IndexError:
        logger.error("No generated found in the LLM's response")
        logger.error(generated_sql_response)
    return generated_sql_response

def change_class_to_str(result):
    try:
        log_info = json.dumps(result.dict(), default=serialize_timestamp)
        return log_info
    except Exception as e:
        logger.error(f"Error in changing class to string: {e}")
        return ""


def serialize_timestamp(obj):
    """
    Custom serialization function for handling objects of types Timestamp and Datetime.date
    :param obj:
    :return:
    """
    if isinstance(obj, pd.Timestamp):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, datetime.date):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, list):
        return [serialize_timestamp(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: serialize_timestamp(v) for k, v in obj.items()}
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')


def convert_timestamps_to_str(data):
    # Convert all Timestamp objects in the data to strings
    try:
        converted_data = []
        for row in data:
            new_row = []
            for item in row:
                if isinstance(item, pd.Timestamp):
                    # Convert Timestamp to string
                    new_row.append(item.strftime('%Y-%m-%d %H:%M:%S'))
                elif isinstance(item, datetime.date):
                    # Convert datetime.date to string
                    new_row.append(item.strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    new_row.append(item)
            converted_data.append(new_row)
        return converted_data
    except Exception as e:
        logger.error(f"Error in converting timestamps to strings: {e}")
        return data
