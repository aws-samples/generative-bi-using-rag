import sqlalchemy as db
from utils.env_var import RDS_MYSQL_HOST, RDS_MYSQL_PORT, RDS_MYSQL_USERNAME, RDS_MYSQL_PASSWORD, RDS_MYSQL_DBNAME, \
    RDS_PQ_SCHEMA


def get_all_table_names(db_url: str, is_sample_db: bool, schema: str = None):
    if is_sample_db:
        print('checking connection...')
        db_url = db_url.format(
            RDS_MYSQL_HOST=RDS_MYSQL_HOST,
            RDS_MYSQL_PORT=RDS_MYSQL_PORT,
            RDS_MYSQL_USERNAME=RDS_MYSQL_USERNAME,
            RDS_MYSQL_PASSWORD=RDS_MYSQL_PASSWORD,
            RDS_MYSQL_DBNAME=RDS_MYSQL_DBNAME,
        )
    engine = db.create_engine(db_url)
    with engine.connect() as connection:
        print('connected to database')

        metadata = db.MetaData()
        if schema:
            metadata.reflect(bind=connection, schema=schema)
        else:
            metadata.reflect(bind=connection)
        tables = metadata.tables
        table_name_list = []

        for table_name, _ in tables.items():
            table_name_list.append(table_name)

    return table_name_list


def get_db_url_dialect(db_url: str) -> str:
    return db_url.split("://")[0].split('+')[0]


def get_dll_for_tables(db_url: str, is_sample_db: bool, schema: str = None, selected_tables: list = []):
    pass