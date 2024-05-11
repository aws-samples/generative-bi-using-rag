import logging

from nlq.data_access.dynamo_query_log import DynamoQueryLogDao

logger = logging.getLogger(__name__)


class LogManagement:
    query_log_dao = DynamoQueryLogDao()

    @classmethod
    def add_log_to_database(cls, log_id, profile_name, sql, query, intent, log_info, time_str):
        cls.query_log_dao.add_log(log_id, profile_name, sql, query, intent, log_info, time_str)
