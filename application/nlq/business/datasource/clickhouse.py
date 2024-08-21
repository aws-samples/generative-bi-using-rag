from nlq.business.datasource.base import DataSourceBase, RowLevelSecurityMode


class ClickHouseDataSource(DataSourceBase):

    def row_level_security_mode(self) -> RowLevelSecurityMode:
        return RowLevelSecurityMode.TABLE_REPLACE

    def support_row_level_security(self) -> bool:
        return True

    def __init__(self):
        super().__init__()