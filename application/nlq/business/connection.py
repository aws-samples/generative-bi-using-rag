from loguru import logger
from nlq.data_access.dynamo_connection import ConnectConfigDao, ConnectConfigEntity
from nlq.data_access.database import RelationDatabase

class ConnectionManagement:
    connection_config_dao = ConnectConfigDao()

    @classmethod
    def get_all_connections(cls):
        logger.info('get all connections...')
        return [conn.conn_name for conn in cls.connection_config_dao.get_db_list()]

    @classmethod
    def add_connection(cls, conn_name, db_type, db_host, db_port, db_user, db_pwd, db_name, comment):
        cls.connection_config_dao.add_url_db(conn_name, db_type, db_host, db_port, db_user, db_pwd, db_name, comment)
        logger.info(f"Connection {conn_name} added")

    @classmethod
    def get_conn_config_by_name(cls, conn_name):
        return cls.connection_config_dao.get_by_name(conn_name)

    @classmethod
    def update_connection(cls, conn_name, db_type, db_host, db_port, db_user, db_pwd, db_name, comment):
        cls.connection_config_dao.update_db_info(conn_name, db_type, db_host, db_port, db_user, db_pwd, db_name, comment)
        logger.info(f"Connection {conn_name} updated")

    @classmethod
    def delete_connection(cls, conn_name):
        if cls.connection_config_dao.delete(conn_name):
            logger.info(f"Connection {conn_name} deleted")
        else:
            logger.warning(f"Failed to delete Connection {conn_name}")

    @classmethod
    def get_table_name_by_config(cls, conn_config: ConnectConfigEntity, schema_names):
        return RelationDatabase.get_all_tables_by_connection(conn_config, schema_names)

    @classmethod
    def get_all_schemas_by_config(cls, conn_config: ConnectConfigEntity):
        return RelationDatabase.get_all_schema_names_by_connection(conn_config)

    @classmethod
    def get_table_definition_by_config(cls, conn_config: ConnectConfigEntity, schema_names, table_names):
        return RelationDatabase.get_table_definition_by_connection(conn_config, schema_names, table_names)

    @classmethod
    def get_db_url_by_name(cls, conn_name):
        conn_config = cls.get_conn_config_by_name(conn_name)
        return RelationDatabase.get_db_url_by_connection(conn_config)