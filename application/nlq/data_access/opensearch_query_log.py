import logging
import os
from utils.env_var import opensearch_info
from utils.opensearch import check_opensearch_index, get_opensearch_cluster_client

logger = logging.getLogger(__name__)

QUERY_LOG_TABLE_NAME = os.getenv("QUERY_LOG_TABLE_NAME", "genbi_query_logging")


class QueryLogEntity:

    def __init__(self, log_id, profile_name, user_id, session_id, sql, query, intent, log_info, time_str,
                 log_type='sql'):
        self.log_id = log_id
        self.profile_name = profile_name
        self.user_id = user_id
        self.session_id = session_id
        self.sql = sql
        self.query = query
        self.intent = intent
        self.log_info = log_info
        self.time_str = time_str
        self.log_type = log_type

    def to_dict(self):
        """Convert to DynamoDB item format"""
        return {
            'log_id': self.log_id,
            'profile_name': self.profile_name,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'sql': self.sql,
            'query': self.query,
            'intent': self.intent,
            'log_info': self.log_info,
            'time_str': self.time_str,
            'log_type': self.log_type
        }


class OpenSearchQueryLogDao:
    def __init__(self):

        self.opensearch_client = get_opensearch_cluster_client(opensearch_info["domain"], opensearch_info["host"],
                                                               opensearch_info["port"],
                                                               opensearch_info["username"], opensearch_info["password"],
                                                               opensearch_info["region"])
        # if not self.exists():
        #     self.create_index()

    def exists(self):
        is_exist = check_opensearch_index(self.opensearch_client, QUERY_LOG_TABLE_NAME)
        return is_exist

    def create_index(self):
        mapping = {
            "mappings": {
                "properties": {
                    "log_id": {
                        "type": "keyword"
                    },
                    "profile_name": {
                        "type": "keyword"
                    },
                    "user_id": {
                        "type": "keyword"
                    },
                    "session_id": {
                        "type": "keyword"
                    },
                    "sql": {
                        "type": "text"
                    },
                    "query": {
                        "type": "text"
                    },
                    "intent": {
                        "type": "keyword"
                    },
                    "log_info": {
                        "type": "text"
                    },
                    "time_str": {
                        "type": "date",
                        "format": "yyyy-MM-dd HH:mm:ss"
                    },
                    "log_type": {
                        "type": "keyword"
                    }
                }
            }
        }
        self.opensearch_client.indices.create(index=QUERY_LOG_TABLE_NAME, body=mapping)

    def add(self, entity: QueryLogEntity):
        try:
            self.opensearch_client.index(index=QUERY_LOG_TABLE_NAME, body=entity.to_dict())
        except Exception as e:
            logger.error("add log entity is error {}", e)

    def add_log(self, log_id, profile_name, user_id, session_id, sql, query, intent, log_info, time_str,
                log_type='sql'):
        entity = QueryLogEntity(log_id, profile_name, user_id, session_id, sql, query, intent, log_info, time_str,
                                log_type)
        self.add(entity)

    def get_logs_by_session(self, profile_name, user_id, session_id, size=3, log_type='sql'):
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"profile_name": profile_name}},
                        {"term": {"session_id": session_id}},
                        {"term": {"user_id": user_id}},
                        {"term": {"log_type": log_type}}
                    ]
                }
            },
            "sort": [
                {"time_str": {"order": "asc"}}
            ],
            "size": size
        }
        response = self.opensearch_client.search(index=QUERY_LOG_TABLE_NAME, body=query)
        history_list = []
        for hit in response.get('hits', {}).get('hits', []):
            history_list.append(hit.get('_source'))
        return history_list

    def get_history_by_user_profile(self, user_id, profile_name, log_type="chat_history"):
        # 目前暂时最多返回10000条历史记录
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"profile_name": profile_name}},
                        {"term": {"user_id": user_id}},
                        {"term": {"log_type": log_type}}
                    ]
                }
            },
            "sort": [
                {"time_str": {"order": "asc"}}
            ],
            "size": 10000
        }
        response = self.opensearch_client.search(index=QUERY_LOG_TABLE_NAME, body=query)
        history_list = []
        for hit in response.get('hits', {}).get('hits', []):
            history_list.append(hit.get('_source'))
        return history_list

    def get_all_history(self, user_id, profile_name, log_type="chat_history"):
        # 获取用户所有的session_id 再通过session_id 获取聊天记录
        query = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"user_id": user_id}},
                        {"term": {"log_type": log_type}},
                        {"term": {"profile_name": profile_name}}
                    ]
                }
            },
            "aggs": {
                "groups": {
                    "terms": {
                        "field": "session_id",
                        "size": 100  # 暂定最多返回100个session_id
                    },
                    "aggs": {
                        "top_hits_agg": {
                            "top_hits": {
                                "size": 1,
                                "_source": {
                                    "includes": ["query", "time_str"]
                                },
                                "sort": [
                                    {"time_str": {"order": "asc"}}
                                ]
                            }
                        }
                    }
                }
            }
        }
        response = self.opensearch_client.search(index=QUERY_LOG_TABLE_NAME, body=query)
        history_list = []
        sorted_history_list = []
        for bucket in response.get('aggregations', {}).get('groups', {}).get('buckets', []):
            session_id = bucket.get('key')
            first_query_info = bucket.get('top_hits_agg', {}).get('hits', {}).get('hits', [])[0].get('_source', {})
            first_query = first_query_info.get('query', session_id)
            first_query_time = first_query_info.get('time_str')
            history_list.append(
                {
                    "session_id": session_id,
                    "title": first_query,
                    "time_str": first_query_time
                }
            )
            sorted_history_list = sorted(history_list, key=lambda x: x['time_str'], reverse=True)
        return sorted_history_list

    def delete_history_by_session(self, user_id, profile_name, session_id):
        try:
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"session_id": session_id}},
                            {"term": {"user_id": user_id}},
                            {"term": {"profile_name": profile_name}}
                        ]
                    }
                }
            }
            self.opensearch_client.delete_by_query(index=QUERY_LOG_TABLE_NAME, body=query)
            return True
        except Exception as e:
            logger.error("delete history by session is error {}", e)
            return False
