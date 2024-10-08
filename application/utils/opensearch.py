import boto3
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
from utils.llm import create_vector_embedding
from utils.env_var import opensearch_info, AOS_INDEX_NER, query_log_name
from utils.logging import getLogger

logger = getLogger()


def get_opensearch_cluster_client(domain, host, port, opensearch_user, opensearch_password, region_name):
    """
    Get an OpenSearch Client
    :param domain:
    :param host:
    :param port:
    :param opensearch_user:
    :param opensearch_password:
    :param region_name:
    :return:
    """
    auth = (opensearch_user, opensearch_password)
    if len(host) == 0:
        host = get_opensearch_endpoint(domain, region_name)

    # Create the client with SSL/TLS enabled, but hostname verification disabled.
    opensearch_client = OpenSearch(
        hosts=[{'host': host, 'port': port}],
        http_compress=True,  # enables gzip compression for request bodies
        http_auth=auth,
        use_ssl=True,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False
    )
    return opensearch_client


def get_opensearch_endpoint(domain, region):
    """
    Get OpenseSearch endpoint
    :param domain:
    :param region:
    :return:
    """
    client = boto3.client('es', region_name=region)
    response = client.describe_elasticsearch_domain(
        DomainName=domain
    )
    return response['DomainStatus']['Endpoint']


def put_bulk_in_opensearch(list, client):
    """
    Put bulk in OpenSearch
    :param list:
    :param client:
    :return:
    """
    logger.info(f"Putting {len(list)} documents in OpenSearch")
    success, failed = bulk(client, list)
    return success, failed


def check_opensearch_index(opensearch_client, index_name):
    """
    Check OpenSearch index
    :param opensearch_client:
    :param index_name:
    :return:
    """
    return opensearch_client.indices.exists(index=index_name)


def create_index(opensearch_client, index_name):
    """
    Create index
    :param opensearch_client:
    :param index_name:
    :return:
    """
    settings = {
        "settings": {
            "index": {
                "knn": True,
                "knn.space_type": "cosinesimil"
            }
        }
    }
    response = opensearch_client.indices.create(index=index_name, body=settings)
    return bool(response['acknowledged'])


def create_index_mapping(opensearch_client, index_name, dimension):
    """
    Create index mapping
    :param opensearch_client:
    :param index_name:
    :param dimension:
    :return:
    """
    response = opensearch_client.indices.put_mapping(
        index=index_name,
        body={
            "properties": {
                "vector_field": {
                    "type": "knn_vector",
                    "dimension": dimension
                },
                "text": {
                    "type": "keyword"
                },
                "profile": {
                    "type": "keyword"
                }
            }
        }
    )
    return bool(response['acknowledged'])

def create_entity_index_mapping(opensearch_client, index_name, dimension):
    """
    Create index mapping
    :param opensearch_client:
    :param index_name:
    :param dimension:
    :return:
    """
    response = opensearch_client.indices.put_mapping(
        index=index_name,
        body={
            "properties": {
                "vector_field": {
                    "type": "knn_vector",
                    "dimension": dimension
                },
                "text": {
                    "type": "keyword"
                },
                "profile": {
                    "type": "keyword"
                },
                "entity_type": {
                    "type": "keyword"
                },
                "entity_count": {
                    "type": "integer"
                },
                "entity_table_info": {
                    "type": "nested",
                    "properties": {
                        "table_name": {
                            "type": "keyword"
                        },
                        "column_name": {
                            "type": "keyword"
                        },
                        "value": {
                            "type": "text"
                        }
                    }
                }
            }
        }
    )
    return bool(response['acknowledged'])


def delete_opensearch_index(opensearch_client, index_name):
    """
    Delete index
    :param opensearch_client:
    :param index_name:
    :return:
    """
    logger.info(f"Trying to delete index {index_name}")
    try:
        response = opensearch_client.indices.delete(index=index_name)
        logger.info(f"Index {index_name} deleted")
        return response['acknowledged']
    except Exception as e:
        logger.info(f"Index {index_name} not found, nothing to delete")
        return True
def check_field_exists(opensearch_client, index_name, field_name):
    """
    Check if a field exists in the specified index
    :param opensearch_client: OpenSearch client
    :param index_name: Name of the index
    :param field_name: Name of the field to check
    :return: True if the field exists, False otherwise
    """
    try:
        # Get the mapping for the index
        mapping = opensearch_client.indices.get_mapping(index=index_name)

        logger.info(mapping)
        # Traverse the mapping to check if the field exists
        if index_name in mapping:
            properties = mapping[index_name]['mappings']['properties']
            if field_name in properties:
                return True
    except Exception as e:
        logger.error(f"Error checking field {field_name}: {e}")

    return False

def get_retrieve_opensearch(opensearch_info, query, search_type, selected_profile, top_k, score_threshold=0.7):
    if search_type == "query":
        index_name = opensearch_info['sql_index']
    elif search_type == "ner":
        index_name = opensearch_info['ner_index']
    else:
        index_name = opensearch_info['agent_index']
    records_with_embedding = create_vector_embedding(query, index_name=index_name)
    retrieve_result = retrieve_results_from_opensearch(
        index_name=index_name,
        region_name=opensearch_info['region'],
        domain=opensearch_info['domain'],
        opensearch_user=opensearch_info['username'],
        opensearch_password=opensearch_info['password'],
        host=opensearch_info['host'],
        port=opensearch_info['port'],
        query_embedding=records_with_embedding['vector_field'],
        top_k=top_k,
        profile_name=selected_profile)

    filter_retrieve_result = []
    for item in retrieve_result:
        if item["_score"] > score_threshold:
            filter_retrieve_result.append(item)
    return filter_retrieve_result


def retrieve_results_from_opensearch(index_name, region_name, domain, opensearch_user, opensearch_password,
                                     query_embedding, top_k=3, host='', port=443, profile_name=None):
    opensearch_client = get_opensearch_cluster_client(domain, host, port, opensearch_user, opensearch_password, region_name)
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
                            "vector_field": {  # Make sure 'vector_field' is the name of your vector field in OpenSearch
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
    response = opensearch_client.search(
        body=search_query,
        index=index_name
    )

    return response['hits']['hits']


def update_index_mapping(opensearch_client, index_name, dimension):
    """
    Create index mapping
    :param opensearch_client:
    :param index_name:
    :param dimension:
    :return:
    """
    response = opensearch_client.indices.put_mapping(
        index=index_name,
        body={
            "properties": {
                "vector_field": {
                    "type": "knn_vector",
                    "dimension": dimension
                },
                "text": {
                    "type": "keyword"
                },
                "profile": {
                    "type": "keyword"
                },
                "entity_type": {
                    "type": "keyword"
                },
                "entity_count": {
                    "type": "integer"
                },
                "entity_table_info": {
                    "type": "nested",
                    "properties": {
                        "table_name": {
                            "type": "keyword"
                        },
                        "column_name": {
                            "type": "keyword"
                        },
                        "value": {
                            "type": "text"
                        }
                    }
                }
            }
        }
    )
    return bool(response['acknowledged'])


def create_log_index(opensearch_client):
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
    opensearch_client.indices.create(index=query_log_name, body=mapping)


def opensearch_index_init():
    """
    OpenSearch index init
    :return:
    """
    try:
        auth = (opensearch_info["username"], opensearch_info["password"])
        host = opensearch_info["host"]
        port = opensearch_info["port"]
        # Create the client with SSL/TLS enabled, but hostname verification disabled.
        opensearch_client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_compress=True,  # enables gzip compression for request bodies
            http_auth=auth,
            use_ssl=True,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False
        )
        index_list = [opensearch_info['sql_index'], opensearch_info['ner_index'], opensearch_info['agent_index']]
        dimension = opensearch_info['embedding_dimension']
        index_create_success = True
        for index_name in index_list:
            exists = check_opensearch_index(opensearch_client, index_name)
            if not exists:
                logger.info("Creating OpenSearch index")
                success = create_index(opensearch_client, index_name)
                if success:
                    logger.info(
                        "Creating OpenSearch index mapping, index is {index_name}".format(index_name=index_name))
                    if index_name == AOS_INDEX_NER:
                        success = create_entity_index_mapping(opensearch_client, index_name, dimension)
                    else:
                        success = create_index_mapping(opensearch_client, index_name, dimension)
                    logger.info(f"OpenSearch Index mapping created")
                else:
                    index_create_success = False
            else:
                if index_name == AOS_INDEX_NER:
                    check_flag = check_field_exists(opensearch_client, index_name, "ner_table_info")
                    logger.info(f"check index flag: {check_flag}")
                    if not check_flag:
                        update_index_mapping(opensearch_client, index_name, dimension)
        exists = check_opensearch_index(opensearch_client, query_log_name)
        if not exists:
            logger.info("genbi_query_logging not exit")
            create_log_index(opensearch_client)
        return index_create_success
    except Exception as e:
        logger.error("create index error")
        logger.error(e)
        return False
