from loguru import logger
import sqlalchemy as db
from sqlalchemy import text, Column

from nlq.data_access.dynamo_connection import ConnectConfigEntity


class RelationDatabase():
    db_mapping = {
        'mysql': 'mysql+pymysql',
        'postgresql': 'postgresql+psycopg2',
        'redshift': 'redshift+psycopg2'
        # Add more mappings here for other databases
    }

    @classmethod
    def get_db_url(cls, db_type, user, password, host, port, db_name):
        db_url = f"{cls.db_mapping[db_type]}://{user}:{password}@{host}:{port}/{db_name}"
        return db_url

    @classmethod
    def test_connection(cls, db_type, user, password, host, port, db_name) -> bool:
        try:
            engine = db.create_engine(cls.get_db_url(db_type, user, password, host, port, db_name))
            connection = engine.connect()
            return True
        except Exception as e:
            logger.exception(e)
            logger.error(f"Failed to connect: {str(e)}")
            return False

    @classmethod
    def get_all_schema_names_by_connection(cls, connection: ConnectConfigEntity):
        schemas = []
        if connection.db_type == 'postgresql':
            db_url = cls.get_db_url(connection.db_type, connection.db_user, connection.db_pwd, connection.db_host,
                                    connection.db_port, connection.db_name)
            engine = db.create_engine(db_url)
            with engine.connect() as conn:
                query = text("""
                    SELECT nspname AS schema_name
                    FROM pg_catalog.pg_namespace
                    WHERE nspname !~ '^pg_' AND nspname <> 'information_schema' AND nspname <> 'public'
                    AND has_schema_privilege(nspname, 'USAGE');
                """)

                # Executing the query
                result = conn.execute(query)
                schemas = [row['schema_name'] for row in result.mappings()]
                print(schemas)

        return schemas

    @classmethod
    def get_all_tables_by_connection(cls, connection: ConnectConfigEntity, schemas=None):
        if schemas is None:
            schemas = []
        metadata = cls.get_metadata_by_connection(connection, schemas)
        return metadata.tables.keys()

    @classmethod
    def get_metadata_by_connection(cls, connection, schemas):
        db_url = cls.get_db_url(connection.db_type, connection.db_user, connection.db_pwd, connection.db_host,
                                connection.db_port, connection.db_name)
        engine = db.create_engine(db_url)
        # connection = engine.connect()
        metadata = db.MetaData()
        for s in schemas:
            metadata.reflect(bind=engine, schema=s)
        metadata.reflect(bind=engine)
        return metadata

    @classmethod
    def get_table_definition_by_connection(cls, connection: ConnectConfigEntity, schemas, table_names):
        metadata = cls.get_metadata_by_connection(connection, schemas)
        tables = metadata.tables
        table_info = {}

        for table_name, table in tables.items():
            # If table name is provided, only generate DDL for those tables. Otherwise, generate DDL for all tables.
            if len(table_names) > 0 and table_name not in table_names:
                continue
            # Start the DDL statement
            table_comment = f'-- {table.comment}' if table.comment else ''
            ddl = f"CREATE TABLE {table_name} {table_comment} \n (\n"
            for column in table.columns:
                column: Column
                # get column description
                column_comment = f'-- {column.comment}' if column.comment else ''
                ddl += f"  {column.name} {column.type.__visit_name__} {column_comment},\n"
            ddl = ddl.rstrip(',\n') + "\n)"  # Remove the last comma and close the CREATE TABLE statement
            table_info[table_name] = {}
            table_info[table_name]['ddl'] = ddl
            table_info[table_name]['description'] = table.comment

            logger.info(f'added table {table_name} to table_info dict')

        return table_info

    @classmethod
    def get_db_url_by_connection(cls, connection: ConnectConfigEntity):
        db_url = cls.get_db_url(connection.db_type, connection.db_user, connection.db_pwd, connection.db_host,
                                connection.db_port, connection.db_name)
        return db_url
