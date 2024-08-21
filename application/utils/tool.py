import json
import logging
import time
import random
import datetime
from multiprocessing import Manager

import pandas as pd

from api.schemas import Message

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

manager = Manager()
shared_data = manager.dict()


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

def get_window_history(user_query_history):
    try:
        history_list = []
        for item in user_query_history:
            if item.type == "human":
                history_list.append("user:" + str(item.content))
            else:
                history_list.append("assistant:" + str(item.content.query_rewrite))
        logger.info(f"history_list: {history_list}")
        return history_list
    except Exception as e:
        logger.error(f"Error in getting window history: {e}")
        return []


def set_share_data(session_id, value):
    shared_data[session_id] = value
    logger.info("Set share data total session is : %s", str(len(shared_data)))


def get_share_data(session_id):
    if session_id in shared_data:
        return shared_data.get(session_id)
    else:
        return []


def update_share_data(session_id, search_box, answer):
    chat_list = []
    if session_id not in shared_data:
        shared_data[session_id] = []
        logger.info("session_id not in shared_data")
        logger.info("Update session_id  is : %s", session_id)
        human_message = Message(type="human", content=search_box)
        bot_message = Message(type="AI", content=answer)
        chat_list.append(human_message)
        chat_list.append(bot_message)
        set_share_data(session_id, chat_list)
        logger.info("not have session is %s, share data length is : %s", session_id, len(shared_data[session_id]))
    else:
        chat_list = shared_data[session_id]
        human_message = Message(type="human", content=search_box)
        bot_message = Message(type="AI", content=answer)
        chat_list.append(human_message)
        chat_list.append(bot_message)
        set_share_data(session_id, chat_list)
        logger.info("have session is %s, share data  is : %s", session_id, len(shared_data[session_id]))