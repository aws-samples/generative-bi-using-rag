import json
import logging

from nlq.data_access.opensearch_query_log import OpenSearchQueryLogDao

logger = logging.getLogger(__name__)


class LogManagement:
    # query_log_dao = DynamoQueryLogDao()
    query_log_dao = OpenSearchQueryLogDao()

    @classmethod
    def add_log_to_database(cls, log_id, user_id, session_id, profile_name, sql, query, intent, log_info, time_str,
                            log_type='chat_history'):
        cls.query_log_dao.add_log(log_id=log_id, profile_name=profile_name, user_id=user_id, session_id=session_id,
                                  sql=sql, query=query, intent=intent, log_info=log_info, time_str=time_str,
                                  log_type=log_type)

    @classmethod
    def get_history(cls, user_id, profile_name, log_type="chat_history"):
        history_list = cls.query_log_dao.get_history_by_user_profile(user_id, profile_name, log_type)
        return history_list

    @classmethod
    def get_history_by_session(cls, session_id, user_id, profile_name, size, log_type):
        user_query_history = []
        history_list = cls.query_log_dao.get_logs_by_session(profile_name=profile_name,
                                                             session_id=session_id,
                                                             user_id=user_id,
                                                             size=size,
                                                             log_type=log_type)
        for log in history_list:
            logger.info("the opensearch log is : {log}".format(log=log))
            answer = json.loads(log['log_info'])
            user_query_history.append("user:" + log['query'])
            user_query_history.append("assistant:" + answer['query_rewrite'])
        return user_query_history

    @classmethod
    def get_all_sessions(cls, user_id, profile_name, log_type):
        session_list = cls.query_log_dao.get_all_history(profile_name=profile_name,
                                                         user_id=user_id,
                                                         log_type=log_type)
        return session_list

    @classmethod
    def get_all_history_by_session(cls, session_id, user_id, profile_name, size, log_type):
        history_list = cls.query_log_dao.get_logs_by_session(profile_name=profile_name,
                                                             session_id=session_id,
                                                             user_id=user_id,
                                                             size=size,
                                                             log_type=log_type)
        return history_list

    @classmethod
    def delete_history_by_session(cls, user_id, profile_name, session_id, log_type="chat_history"):
        return cls.query_log_dao.delete_history_by_session(user_id, profile_name, session_id)