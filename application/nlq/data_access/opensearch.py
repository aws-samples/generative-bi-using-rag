import logging

from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk

from utils.llm import create_vector_embedding_with_bedrock

logger = logging.getLogger(__name__)

def put_bulk_in_opensearch(list, client):
    logger.info(f"Putting {len(list)} documents in OpenSearch")
    success, failed = bulk(client, list)
    return success, failed

class OpenSearchDao:

    def __init__(self, host, port, opensearch_user, opensearch_password):
        auth = (opensearch_user, opensearch_password)

        # Create the client with SSL/TLS enabled, but hostname verification disabled.
        self.opensearch_client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_compress=True,  # enables gzip compression for request bodies
            http_auth=auth,
            use_ssl=True,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False
        )

    def retrieve_samples(self, index_name, profile_name):
        # search all docs in the index filtered by profile_name
        search_query = {
            "sort": [
                {
                    "_score": {
                        "order": "desc"
                    }
                }
            ],
            "_source": {
                "includes": ["text", "sql"]
            },
            "size": 5000,
            "query": {
                "bool": {
                    "must": [],
                    "filter": [
                        {
                            "match_all": {}
                        },
                        {
                            "match_phrase": {
                                "profile": profile_name
                            }
                        }
                    ],
                    "should": [],
                    "must_not": []
                }
            }
        }

        # Execute the search query
        response = self.opensearch_client.search(
            body=search_query,
            index=index_name
        )

        return response['hits']['hits']

    def retrieve_entity_samples(self, index_name, profile_name):
        # search all docs in the index filtered by profile_name
        search_query = {
            "sort": [
                {
                    "_score": {
                        "order": "desc"
                    }
                }
            ],
            "_source": {
                "includes": ["entity", "comment"]
            },
            "size": 5000,
            "query": {
                "bool": {
                    "must": [],
                    "filter": [
                        {
                            "match_all": {}
                        },
                        {
                            "match_phrase": {
                                "profile": profile_name
                            }
                        }
                    ],
                    "should": [],
                    "must_not": []
                }
            }
        }

        response = self.opensearch_client.search(
        body=search_query,
        index=index_name
        )

        return response['hits']['hits']

    def retrieve_agent_cot_samples(self, index_name, profile_name):
        # search all docs in the index filtered by profile_name
        search_query = {
            "sort": [
                {
                    "_score": {
                        "order": "desc"
                    }
                }
            ],
            "_source": {
                "includes": ["query", "comment"]
            },
            "size": 5000,
            "query": {
                "bool": {
                    "must": [],
                    "filter": [
                        {
                            "match_all": {}
                        },
                        {
                            "match_phrase": {
                                "profile": profile_name
                            }
                        }
                    ],
                    "should": [],
                    "must_not": []
                }
            }
        }

        # Execute the search query
        response = self.opensearch_client.search(
        body=search_query,
        index=index_name
        )

        return response['hits']['hits']

    def add_sample(self, index_name, profile_name, question, answer, embedding):
        record = {
            '_index': index_name,
            'text': question,
            'sql': answer,
            'profile': profile_name,
            'vector_field': embedding
        }

        success, failed = put_bulk_in_opensearch([record], self.opensearch_client)
        return success == 1

    def add_entity_sample(self, index_name, profile_name, entity, comment, embedding, entity_type="", entity_table_info=[]):
        entity_count = len(entity_table_info)
        comment_value = []
        item_comment_format = "{entity} is located in table {table_name}, column {column_name},  the dimension value is {value}."
        if entity_type == "dimension":
            if entity_count > 0:
                for item in entity_table_info:
                    table_name = item["table_name"]
                    column_name = item["column_name"]
                    value = item["value"]
                    comment_format = item_comment_format.format(entity=entity, table_name=table_name,
                                                                column_name=column_name, value=value)
                    comment_value.append(comment_format)
            comment = ";".join(comment_value)

        record = {
            '_index': index_name,
            'entity': entity,
            'comment': comment,
            'profile': profile_name,
            'vector_field': embedding,
            'entity_type': entity_type,
            'entity_count': entity_count,
            'entity_table_info': entity_table_info
        }

        success, failed = put_bulk_in_opensearch([record], self.opensearch_client)
        return success == 1

    def add_agent_cot_sample(self, index_name, profile_name, query, comment, embedding):
        record = {
            '_index': index_name,
            'query': query,
            'comment': comment,
            'profile': profile_name,
            'vector_field': embedding
        }

        success, failed = put_bulk_in_opensearch([record], self.opensearch_client)
        return success == 1

    def delete_sample(self, index_name, profile_name, doc_id):
        return self.opensearch_client.delete(index=index_name, id=doc_id)

    def search_sample(self, profile_name, top_k, index_name, query):
        records_with_embedding = create_vector_embedding_with_bedrock(query, index_name=index_name)
        return self.search_sample_with_embedding(profile_name, top_k, index_name,  records_with_embedding['vector_field'])


    def search_sample_with_embedding(self, profile_name, top_k, index_name, query_embedding):
        search_query = {
            "size": top_k,  # Adjust the size as needed to retrieve more or fewer results
            "query": {
                "bool": {
                    "filter": {
                        "match_phrase": {
                            "profile": profile_name
                        }
                    },
                    "must": [
                        {
                            "knn": {
                                "vector_field": {
                                    # Make sure 'vector_field' is the name of your vector field in OpenSearch
                                    "vector": query_embedding,
                                    "k": top_k  # Adjust k as needed to retrieve more or fewer nearest neighbors
                                }
                            }
                        }
                    ]
                }

            }
        }

        # Execute the search query
        response = self.opensearch_client.search(
            body=search_query,
            index=index_name
        )

        return response['hits']['hits']
