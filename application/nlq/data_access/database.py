import logging
import re
from typing import Optional, List

import sqlalchemy as db
from sqlalchemy import Column
from sqlalchemy.engine import Inspector, Engine
from sqlalchemy.sql.ddl import CreateTable

from nlq.data_access.dynamo_connection import ConnectConfigEntity

logger = logging.getLogger(__name__)

db_mapping = {
            'mysql': 'mysql+pymysql',
            'postgresql': 'postgresql+psycopg2',
            'redshift': 'postgresql+psycopg2',
            'starrocks': 'starrocks',
            'clickhouse': 'clickhouse',
            # Add more mappings here for other databases
        }


class RelationDatabase:
    def __init__(self, connection: ConnectConfigEntity = None):
        self.connection = connection

    def get_sqla_engine(self) -> Engine:
        engine = db.create_engine(self.db_url)
        return engine

    @property
    def inspector(self) -> Inspector:
        engine = self.get_sqla_engine()
        return db.inspect(engine)

    @staticmethod
    def get_db_url(db_type, user, password, host, port, db_name):
        db_url = db.engine.URL.create(
            drivername=db_mapping[db_type],
            username=user,
            password=password,
            host=host,
            port=port,
            database=db_name
        )
        return db_url

    @property
    def db_url(self):
        return self.get_db_url(self.connection.db_type, self.connection.db_user, self.connection.db_pwd,
                               self.connection.db_host,
                               self.connection.db_port, self.connection.db_name)

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

    def get_all_schema_names_by_connection(self):
        db_type = self.connection.db_type
        if db_type == 'postgresql':
            schemas = [schema for schema in self.inspector.get_schema_names() if
                       schema not in ('pg_catalog', 'information_schema', 'public')]
        elif db_type in ('redshift', 'mysql', 'starrocks', 'clickhouse'):
            schemas = self.inspector.get_schema_names()
        else:
            raise ValueError("Unsupported database type")

        return schemas

    def get_all_tables_by_connection(self, schemas=None):
        if schemas is None:
            schemas = []
        metadata = self.get_metadata_by_connection(schemas)
        return [table.fullname for key, table in metadata.tables.items()]

    def get_metadata_by_connection(self, schemas):
        engine = self.get_sqla_engine()
        metadata = db.MetaData()
        for s in schemas:
            metadata.reflect(views=True, bind=engine, schema=s)
        metadata.reflect(bind=engine)
        return metadata

    def get_table_definition_by_connection(self, schemas, table_names):
        metadata = self.get_metadata_by_connection(schemas)
        tables = metadata.tables
        table_info = {}
        engine = self.get_sqla_engine()
        for key, table in tables.items():
            # If table name is provided, only generate DDL for those tables. Otherwise, generate DDL for all tables.
            table_name = table.fullname
            if len(table_names) > 0 and table_name not in table_names:
                continue
            table_info[table_name] = {}
            try:
                create_table = str(CreateTable(table).compile(engine))
                ddl = f"{create_table.rstrip()}"
            except:
                table_comment = f'-- {table.comment}' if table.comment else ''
                ddl = f"CREATE TABLE {table_name} {table_comment} \n (\n"
                for column in table.columns:
                    column: Column
                    column_comment = f'-- {column.comment}' if column.comment else ''
                    ddl += f"  {column.name} {column.type.__visit_name__} {column_comment},\n"
                ddl = ddl.rstrip(',\n') + "\n)"

            table_info[table_name]['ddl'] = ddl
            table_info[table_name]['description'] = table.comment
            table_info[table_name]['database_id'] = int(self.connection.id)

            logger.info(f'added table {table_name} to table_info dict')

        return table_info