import logging
import pandas as pd
from nlq.business.connection import ConnectionManagement
from utils.apis import query_from_sql_pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_response_sql(generated_sql_response):
    try:
        return generated_sql_response.split("<sql>")[1].split("</sql>")[0]
    except IndexError:
        logger.error("get_response_sql is error")
        logger.info(generated_sql_response)
        return ""


def get_sql_result_tool(profile, sql):
    try:
        db_url = profile['db_url']
        if not db_url:
            conn_name = profile['conn_name']
            db_url = ConnectionManagement.get_db_url_by_name(conn_name)
        executed_result_df = query_from_sql_pd(p_db_url=db_url, query=sql)

        return executed_result_df
    except Exception as e:
        logger.error("get_sql_result is error: {}".format(e))
    return pd.DataFrame()
