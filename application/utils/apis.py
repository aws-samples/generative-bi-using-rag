import sqlalchemy as db
from sqlalchemy import text
from utils.env_var import RDS_MYSQL_HOST, RDS_MYSQL_PORT, RDS_MYSQL_USERNAME, RDS_MYSQL_PASSWORD, RDS_MYSQL_DBNAME, RDS_PQ_SCHEMA
import pandas as pd
import logging
import sqlparse
from nlq.business.connection import ConnectionManagement

logger = logging.getLogger(__name__)

ALLOWED_QUERY_TYPES = ['SELECT']
def query_from_database(p_db_url: str, query, schema=None):
    """
    Query the database
    """
    try:
        if '{RDS_MYSQL_USERNAME}' in p_db_url:
            engine = db.create_engine(p_db_url.format(
                RDS_MYSQL_HOST=RDS_MYSQL_HOST,
                RDS_MYSQL_PORT=RDS_MYSQL_PORT,
                RDS_MYSQL_USERNAME=RDS_MYSQL_USERNAME,
                RDS_MYSQL_PASSWORD=RDS_MYSQL_PASSWORD,
                RDS_MYSQL_DBNAME=RDS_MYSQL_DBNAME,
            ))
        else:
            engine = db.create_engine(p_db_url)
        with engine.connect() as connection:
            logger.info(f'{query=}')
            sanitized_query = sqlparse.format(query, strip_comments=True)
            query_type = sqlparse.parse(sanitized_query)[0].get_type()
            if query_type not in ALLOWED_QUERY_TYPES:
                return {"status": "error", "message": f"Query type '{query_type}' is not allowed."}
            # if schema and 'postgres' in p_db_url:
            #     query = f'SET search_path TO {schema}; {query}'
            cursor = connection.execute(text(sanitized_query))
            results = cursor.fetchall()
            columns = list(cursor.keys())
    except ValueError as e:
        logger.exception(e)
        return {"status": "error", "message": str(e)}
    return {
        "status": "ok",
        "data": str(results),
        "query": sanitized_query,
        "columns": columns
    }


def query_from_sql_pd(p_db_url: str, query, schema=None):
    """
    Query the database
    """
    if '{RDS_MYSQL_USERNAME}' in p_db_url:
        engine = db.create_engine(p_db_url.format(
            RDS_MYSQL_HOST=RDS_MYSQL_HOST,
            RDS_MYSQL_PORT=RDS_MYSQL_PORT,
            RDS_MYSQL_USERNAME=RDS_MYSQL_USERNAME,
            RDS_MYSQL_PASSWORD=RDS_MYSQL_PASSWORD,
            RDS_MYSQL_DBNAME=RDS_MYSQL_DBNAME,
        ))
    else:
        engine = db.create_engine(p_db_url)

    with engine.connect() as connection:
        logger.info(f'{query=}')
        res = pd.DataFrame()
        try:
            res = pd.read_sql_query(text(query), connection)
        except Exception as e:
            logger.error("query_from_sql_pd is error")
            logger.error(e)
        return res

def get_sql_result_tool(profile, sql):
    result_dict = {"data": pd.DataFrame(), "sql": sql, "status_code": 200, "error_info": ""}
    try:
        p_db_url = profile['db_url']
        if not p_db_url:
            conn_name = profile['conn_name']
            p_db_url = ConnectionManagement.get_db_url_by_name(conn_name)

        if '{RDS_MYSQL_USERNAME}' in p_db_url:
            engine = db.create_engine(p_db_url.format(
                RDS_MYSQL_HOST=RDS_MYSQL_HOST,
                RDS_MYSQL_PORT=RDS_MYSQL_PORT,
                RDS_MYSQL_USERNAME=RDS_MYSQL_USERNAME,
                RDS_MYSQL_PASSWORD=RDS_MYSQL_PASSWORD,
                RDS_MYSQL_DBNAME=RDS_MYSQL_DBNAME,
            ))
        else:
            engine = db.create_engine(p_db_url)
        with engine.connect() as connection:
            logger.info(f'{sql=}')
            executed_result_df = pd.read_sql_query(text(sql), connection)
            result_dict["data"] = executed_result_df
    except Exception as e:
        logger.error("get_sql_result is error: {}".format(e))
        result_dict["error_info"] = e
        result_dict["status_code"] = 500
    return result_dict
