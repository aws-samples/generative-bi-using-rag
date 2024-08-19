import yaml
from abc import ABC, abstractmethod

from nlq.business.login_user import LoginUser
from utils.apis import replace_table_with_subquery
from utils.logging import getLogger

logger = getLogger()

class RowLevelSecurityMode:
    NONE = None
    TABLE_REPLACE = 'TABLE_REPLACE'


class DataSourceBase(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def support_row_level_security(self) -> bool:
        pass

    @abstractmethod
    def row_level_security_mode(self) -> RowLevelSecurityMode:
        pass

    # @abstractmethod
    def row_level_security_control(self, sql: str, rls_config: str, login_user: LoginUser) -> str:
        print('rls_config', rls_config)
        replaced_sql = sql
        rls_config_obj = {'tables': []}
        try:
            if rls_config:
                rls_config_obj = yaml.safe_load(rls_config)
            # YAML format:
            # {'tables': [{'table_name': 'table_a', 'columns': [
            # {'column_name': 'username', 'column_value': '$login_user.username'}]}]}
            for table in rls_config_obj['tables']:
                table_name = table['table_name']
                columns = table['columns']
                for column in columns:
                    column_name = column['column_name']
                    column_value = column['column_value']

                    if column_value == '$login_user.username' and login_user is not None:
                        column_value = login_user.get_username()

                    replaced_sql = replace_table_with_subquery(sql, table_name, column_name, column_value)
        except Exception as e:
            logger.exception('Failed to apply RLS config')
            logger.info(f'{sql=}')
            logger.info(f'{rls_config=}')
            logger.info(f'{login_user=}')

        return replaced_sql

    def post_sql_generation(self, sql: str, rls_config: str = None, login_user: LoginUser = None) -> str:
        if self.row_level_security_mode() != RowLevelSecurityMode.NONE:
            return self.row_level_security_control(sql, rls_config, login_user)
        # 默认直接返回输入的SQL
        return sql
