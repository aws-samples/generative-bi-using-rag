import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.helpers import bulk
import logging
from utils.llm import create_vector_embedding_with_bedrock
from utils.env_var import opensearch_info

logger = logging.getLogger(__name__)


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


def get_retrieve_opensearch(opensearch_info, query, search_type, selected_profile, top_k, score_threshold=0.7):
    if search_type == "query":
        index_name = opensearch_info['sql_index']
    elif search_type == "ner":
        index_name = opensearch_info['ner_index']
    else:
        index_name = opensearch_info['agent_index']

    records_with_embedding = create_vector_embedding_with_bedrock(
        query, index_name=index_name)
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


def upload_results_to_opensearch(region_name, domain, opensearch_user, opensearch_password, index_name, query, sql,
                                 host='', port=443):

    opensearch_client = get_opensearch_cluster_client(domain, host, port, opensearch_user, opensearch_password, region_name)

    # Vector embedding using Amazon Bedrock Titan text embedding
    logger.info(f"Creating embeddings for records")
    record_with_embedding = create_vector_embedding_with_bedrock(query, index_name)

    record_with_embedding['sql'] = sql
    success, failed = put_bulk_in_opensearch([record_with_embedding], opensearch_client)
    if success == 1:
        logger.info("Finished creating records using Amazon Bedrock Titan text embedding")
        return True
    else:
        logger.error("Failed to create records using Amazon Bedrock Titan text embedding")
        return False


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
                    success = create_index_mapping(opensearch_client, index_name, dimension)
                    logger.info(f"OpenSearch Index mapping created")
                else:
                    index_create_success = False
        return index_create_success
    except Exception as e:
        logger.error("create index error")
        logger.error(e)
        return False
