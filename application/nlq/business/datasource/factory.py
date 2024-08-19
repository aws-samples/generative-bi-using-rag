from nlq.business.datasource.clickhouse import ClickHouseDataSource
from nlq.business.datasource.base import DataSourceBase
from nlq.business.datasource.default import DefaultDataSoruce
from nlq.business.datasource.mysql import MySQLDataSource


class DataSourceFactory:

    @staticmethod
    def get_data_source(data_source_type) -> DataSourceBase:
        if data_source_type == "mysql":
            return MySQLDataSource()
        elif data_source_type == "clickhouse":
            return ClickHouseDataSource()
        else:
            return DefaultDataSoruce()