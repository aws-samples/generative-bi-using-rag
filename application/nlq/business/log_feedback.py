import json
import logging

from nlq.data_access.dynamo_query_log import DynamoQueryLogDao
from utils.logging import getLogger

logger = getLogger()


class FeedBackManagement:
    dynammo_log_dao = DynamoQueryLogDao()

    @classmethod
    def add_log_to_database(cls, log_id, user_id, session_id, profile_name, sql, query, intent, log_info, time_str,
                            log_type='chat_history'):
        cls.dynammo_log_dao.add_log(log_id=log_id, profile_name=profile_name, user_id=user_id, session_id=session_id,
                                  sql=sql, query=query, intent=intent, log_info=log_info, time_str=time_str,
                                  log_type=log_type)