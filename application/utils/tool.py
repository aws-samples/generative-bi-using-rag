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
    # 获取当前时间戳，精确到微秒
    timestamp = int(time.time() * 1000000)
    # 添加随机数以增加唯一性
    random_part = random.randint(0, 9999)
    # 拼接时间戳和随机数生成logID
    log_id = f"{timestamp}{random_part:04d}"
    return log_id


def get_current_time():
    # 获取当前时间
    now = datetime.now()
    # 格式化时间，包括毫秒部分
    # 注意：strftime默认不直接支持毫秒，需要单独处理
    formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time


def get_generated_sql_explain(generated_sql_response):
    index = generated_sql_response.find("</sql>")
    if index != -1:
        return generated_sql_response[index + len("</sql>"):]
    else:
        return generated_sql_response
