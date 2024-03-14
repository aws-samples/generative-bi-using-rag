import sqlalchemy as db
from sqlalchemy import text
from utils.env_var import RDS_MYSQL_HOST, RDS_MYSQL_PORT, RDS_MYSQL_USERNAME, RDS_MYSQL_PASSWORD, RDS_MYSQL_DBNAME, RDS_PQ_SCHEMA
import pandas as pd
from loguru import logger


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
            # if schema and 'postgres' in p_db_url:
            #     query = f'SET search_path TO {schema}; {query}'
            cursor = connection.execute(text(query))
            results = cursor.fetchall()
            columns = list(cursor.keys())
    except ValueError as e:
        logger.exception(e)
        return {"status": "error", "message": str(e)}
    return {
        "status": "ok",
        "data": str(results),
        "query": query,
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
        # if schema and 'postgres' in p_db_url:
        #     query = f'SET search_path TO {RDS_PQ_SCHEMA}; {query}'
        return pd.read_sql_query(text(query), connection)
