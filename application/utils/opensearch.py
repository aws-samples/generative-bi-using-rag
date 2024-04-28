import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.helpers import bulk
import logging
from utils.llm import create_vector_embedding_with_bedrock, retrieve_results_from_opensearch

logger = logging.getLogger(__name__)

def get_opensearch_cluster_client(domain, user, password, region, index_name):
    opensearch_endpoint = get_opensearch_endpoint(domain, region)
    opensearch_client = OpenSearch(
        hosts=[{
            'host': opensearch_endpoint,
            'port': 443
            }],
        http_auth=(user, password),
        index_name = index_name,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30
        )
    return opensearch_client
    
def get_opensearch_endpoint(domain, region):
    client = boto3.client('es', region_name=region)
    response = client.describe_elasticsearch_domain(
        DomainName=domain
    )
    return response['DomainStatus']['Endpoint']

def put_bulk_in_opensearch(list, client):
    logger.info(f"Putting {len(list)} documents in OpenSearch")
    success, failed = bulk(client, list)
    return success, failed

def check_opensearch_index(opensearch_client, index_name):
    return opensearch_client.indices.exists(index=index_name)

def create_index(opensearch_client, index_name):
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
    logger.info(f"Trying to delete index {index_name}")
    try:
        response = opensearch_client.indices.delete(index=index_name)
        logger.info(f"Index {index_name} deleted")
        return response['acknowledged']
    except Exception as e:
        logger.info(f"Index {index_name} not found, nothing to delete")
        return True

def get_retrieve_opensearch(env_vars, query, search_type, selected_profile, top_k, score_threshold=0.7):
    demo_profile_suffix = '(demo)'
    origin_selected_profile = selected_profile
    selected_profile = "shopping_guide"

    if search_type == "query":
        index_name = env_vars['data_sources'][selected_profile]['opensearch']['index_name']
    elif search_type == "ner":
        index_name = env_vars['data_sources'][selected_profile]['opensearch']['index_name'] + "_ner"
    else:
        index_name = env_vars['data_sources'][selected_profile]['opensearch']['index_name'] + "_agent"

    records_with_embedding = create_vector_embedding_with_bedrock(
        query,
        index_name=env_vars['data_sources'][selected_profile]['opensearch']['index_name'])
    retrieve_result = retrieve_results_from_opensearch(
        index_name=index_name,
        region_name=env_vars['data_sources'][selected_profile]['opensearch']['region_name'],
        domain=env_vars['data_sources'][selected_profile]['opensearch']['domain'],
        opensearch_user=env_vars['data_sources'][selected_profile]['opensearch'][
            'opensearch_user'],
        opensearch_password=env_vars['data_sources'][selected_profile]['opensearch'][
            'opensearch_password'],
        host=env_vars['data_sources'][selected_profile]['opensearch'][
            'opensearch_host'],
        port=env_vars['data_sources'][selected_profile]['opensearch'][
            'opensearch_port'],
        query_embedding=records_with_embedding['vector_field'],
        top_k=top_k,
        profile_name=origin_selected_profile.replace(demo_profile_suffix, ''))

    selected_profile = origin_selected_profile

    filter_retrieve_result = []
    for item in retrieve_result:
        if item["_score"] > score_threshold:
            filter_retrieve_result.append(item)
    return filter_retrieve_result

