from nlq.business.datasource.base import DataSourceBase, RowLevelSecurityMode


class DefaultDataSoruce(DataSourceBase):

    def row_level_security_mode(self) -> RowLevelSecurityMode:
        return RowLevelSecurityMode.NONE

    def support_row_level_security(self) -> bool:
        return False

    def __init__(self):
        super().__init__()
