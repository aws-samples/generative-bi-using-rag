import yaml
from abc import ABC, abstractmethod

from nlq.business.login_user import LoginUser
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
        """Abstract method to check if row-level security is supported"""
        pass

    @abstractmethod
    def row_level_security_mode(self) -> RowLevelSecurityMode:
        """Abstract method to get the row-level security mode"""
        pass

    @staticmethod
    def validate_row_level_security_config(rls_config: str) -> bool:
        """method to validate row-level security config"""
        try:
            DataSourceBase.convert_rls_yaml_to_table_subquery(LoginUser('validate_user'), yaml.safe_load(rls_config))
            return True
        except Exception as e:
            logger.error(f'Failed to validate RLS config:\n{rls_config}')
            return False

    def row_level_security_control(self, sql: str, rls_config: str, login_user: LoginUser) -> str:
        """Method to apply row-level security control"""
        replaced_sql = sql
        rls_config_obj = {'tables': []}
        try:
            if rls_config:
                rls_config_obj = yaml.safe_load(rls_config)
            # YAML format:
            # {'tables': [{'table_name': 'table_a', 'columns': [
            # {'column_name': 'username', 'column_value': '$login_user.username'}]}]}
            table_statements = self.convert_rls_yaml_to_table_subquery(login_user, rls_config_obj)

            logger.info(f'original SQL: {sql}')
            replaced_sql = self.replace_table_with_cte(sql, table_statements)
            logger.info(f'RLS applied SQL: {replaced_sql}')
        except Exception as e:
            logger.exception('Failed to apply RLS config')
            logger.info(f'{sql=}')
            logger.info(f'{rls_config=}')
            logger.info(f'{login_user=}')

        return replaced_sql

    @staticmethod
    def convert_rls_yaml_to_table_subquery(login_user, rls_config_obj):
        """method to convert RLS YAML to table subqueries"""
        table_statements = {}
        for table in rls_config_obj['tables']:
            table_name = table['table_name']

            condition = ''
            columns = table['columns']
            for column in columns:
                column_name = column['column_name']
                column_value = column['column_value']

                if column_value == '$login_user.username' and login_user is not None:
                    column_value = login_user.get_username()

                if not condition:
                    condition += condition + f"{column_name} = '{column_value}'"
                else:
                    condition += condition + f" AND {column_name} = '{column_value}'"

            statement = f'(SELECT * FROM {table_name} WHERE {condition})'
            table_statements[table_name] = statement
        return table_statements

    @staticmethod
    def replace_table_with_cte(sql, table_config: dict):
        """method to replace tables with CTEs"""
        cte_sql = ''
        sql_splits = ['']
        origin_sql_has_cte = False
        if 'with' in sql:
            sql_splits = sql.split('with')
            origin_sql_has_cte = True
        elif 'WITH' in sql:
            sql_splits = sql.split('WITH')
            origin_sql_has_cte = True
        else:
            # cte_sql = "WITH\n"
            sql_splits.append(sql)

        for table_name, sub_query in table_config.items():
            cte_sql += f"/* rls applied */ {table_name} AS {sub_query},\n"
        if origin_sql_has_cte:
            cte_sql = cte_sql[:-1]
        else:
            cte_sql = cte_sql[:-2]

        return f'''WITH
{cte_sql}
{sql_splits[1]}'''

    def post_sql_generation(self, sql: str, rls_config: str = None, login_user: LoginUser = None) -> str:
        """Method to post-process SQL after generation"""
        if self.row_level_security_mode() != RowLevelSecurityMode.NONE and rls_config is not None:
            return self.row_level_security_control(sql, rls_config, login_user)
        # 默认直接返回输入的SQL
        return sql
