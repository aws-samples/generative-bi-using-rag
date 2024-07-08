import logging
import time
import random
from datetime import datetime

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
    now = datetime.now()
    formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time


def get_generated_sql_explain(generated_sql_response):
    index = generated_sql_response.find("</sql>")
    if index != -1:
        return generated_sql_response[index + len("</sql>"):]
    else:
        return generated_sql_response
