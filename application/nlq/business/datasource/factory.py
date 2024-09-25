from nlq.business.datasource.clickhouse import ClickHouseDataSource
from nlq.business.datasource.base import DataSourceBase
from nlq.business.datasource.default import DefaultDataSoruce
from nlq.business.datasource.mysql import MySQLDataSource
from nlq.business.login_user import LoginUser


class DataSourceFactory:

    @staticmethod
    def get_data_source(data_source_type) -> DataSourceBase:
        if data_source_type == "mysql":
            return MySQLDataSource()
        elif data_source_type == "clickhouse":
            return ClickHouseDataSource()
        else:
            return DefaultDataSoruce()

    @staticmethod
    def apply_row_level_security_for_sql(db_type: str, sql: str, rls_config: str, username: str):
        data_source = DataSourceFactory.get_data_source(db_type)
        post_sql = data_source.post_sql_generation(
            sql,
            rls_config=rls_config,
            login_user=LoginUser(username))
        return post_sql
