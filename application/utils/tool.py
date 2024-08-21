import json
import logging
import time
import random
import datetime

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_generated_sql(generated_sql_response):
    sql = ""
    try:
        return generated_sql_response.split("<sql>")[1].split("</sql>")[0]
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
    index = generated_sql_response.find("</sql>")
    if index != -1:
        return generated_sql_response[index + len("</sql>"):]
    else:
        return generated_sql_response


def change_class_to_str(result):
    try:
        log_info = json.dumps(result.dict())
        return log_info
    except Exception as e:
        logger.error(f"Error in changing class to string: {e}")
        return ""


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
