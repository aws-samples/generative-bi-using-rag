import logging

from nlq.data_access.dynamo_query_log import DynamoQueryLogDao

logger = logging.getLogger(__name__)


class LogManagement:
    query_log_dao = DynamoQueryLogDao()

    @classmethod
    def add_log_to_database(cls, log_id, user_id, session_id, profile_name, sql, query, intent, log_info, time_str,
                            log_type="normal_log", ):
        cls.query_log_dao.add_log(log_id=log_id, profile_name=profile_name, user_id=user_id, session_id=session_id,
                                  sql=sql, query=query, intent=intent, log_info=log_info, log_type=log_type,
                                  time_str=time_str)

    @classmethod
    def get_history(cls, user_id, profile_name):
        history_list = cls.query_log_dao.get_history_by_user_profile(user_id, profile_name)
        return history_list
