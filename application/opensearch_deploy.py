import json
from utils import opensearch
from opensearchpy import OpenSearch
from dotenv import load_dotenv
import os
import boto3
import sys

load_dotenv()

AOS_HOST = os.getenv('AOS_HOST', '')
AOS_PORT = os.getenv('AOS_PORT', 9200)
AOS_USER = os.getenv('AOS_USER', 'admin')
AOS_PASSWORD = os.getenv('AOS_PASSWORD', 'admin')
AOS_DOMAIN = os.getenv('AOS_DOMAIN', 'llm-data-analytics')
AOS_REGION = os.getenv('AOS_REGION')
AOS_INDEX = os.getenv('AOS_INDEX', 'uba')
AOS_TYPE = os.getenv('AOS_TYPE', 'uba')
BEDROCK_REGION = os.getenv('BEDROCK_REGION')

REGION_NAME = AOS_REGION
early_stop_record_count = 100
index_name = AOS_INDEX
opensearch_user = AOS_USER
opensearch_password = AOS_PASSWORD
# create opensearch domain
domain = AOS_DOMAIN

def index_to_opensearch():
    create_index = True
    if len(sys.argv) == 1:
        from deployment.default_index_data import bulk_questions
        print(f'found {len(bulk_questions)} questions in default collection')
    elif 2 <= len(sys.argv) < 4:
        from deployment.custom_index_data_sample import custom_bulk_questions
        bulk_questions = custom_bulk_questions[sys.argv[1]]
        print(f'found {len(bulk_questions)} questions in {sys.argv[1]} collection')
        if len(sys.argv) == 3 and sys.argv[2] == 'false':
            create_index = False
    else:
        print('Usage: python3 opensearch_deploy.py <collection_name> <create_index:bool>')
        print('       create_index: true (default) or false')
        return

    if AOS_HOST == '':
        # add a new opensearch domain named llm-data-analytics in us-west-2
        client = boto3.client('opensearch', region_name=REGION_NAME)
        client.create_domain(
            DomainName='llm-data-analytics',
            EngineVersion='OpenSearch_2.7',
            NodeToNodeEncryptionOptions={
                'Enabled': True
            },
            EncryptionAtRestOptions={
                'Enabled': True
            },
            AdvancedSecurityOptions={
                'Enabled': True,
                'InternalUserDatabaseEnabled': True,
                'MasterUserOptions': {
                    'MasterUserName': 'admin',
                    'MasterUserPassword': 'Admin&123'
                }
            },
            DomainEndpointOptions={
                'EnforceHTTPS': True
            },
            EBSOptions={
                'EBSEnabled': True,
                'VolumeType': 'gp2',
                'VolumeSize': 10
            }
        )

        # initiate AWS OpenSearch client and insert new data into the index
        opensearch_client = opensearch.get_opensearch_cluster_client(domain, opensearch_user, opensearch_password,
                                                                     REGION_NAME,
                                                                     index_name)
    else:
        auth = (opensearch_user, opensearch_password)
        host = AOS_HOST
        port = AOS_PORT
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

    def create_vector_embedding_with_bedrock(text, index_name, bedrock_client):
        payload = {"inputText": f"{text}"}
        body = json.dumps(payload)
        modelId = "amazon.titan-embed-text-v1"
        accept = "application/json"
        contentType = "application/json"

        response = bedrock_client.invoke_model(
            body=body, modelId=modelId, accept=accept, contentType=contentType
        )
        response_body = json.loads(response.get("body").read())

        embedding = response_body.get("embedding")
        return {"_index": index_name, "text": text, "vector_field": embedding}


    def get_bedrock_client(region):
        bedrock_client = boto3.client("bedrock-runtime", region_name=region)
        return bedrock_client


    # Check if to delete OpenSearch index with the argument passed to the script --recreate 1
    # response = opensearch.delete_opensearch_index(opensearch_client, name)

    exists = opensearch.check_opensearch_index(opensearch_client, index_name)
    if not exists:
        print("Creating OpenSearch index")
        success = opensearch.create_index(opensearch_client, index_name)
        if success:
            print("Creating OpenSearch index mapping")
            success = opensearch.create_index_mapping(opensearch_client, index_name)
            print(f"OpenSearch Index mapping created")
    else:
        if create_index:
            print("Index already exists. Exit with 0 now.")
            exit(0)

    all_records = bulk_questions

    # Initialize bedrock client
    bedrock_client = get_bedrock_client(BEDROCK_REGION)

    # Vector embedding using Amazon Bedrock Titan text embedding
    all_json_records = []
    print(f"Creating embeddings for records")

    # using the arg --early-stop
    i = 0
    for record in all_records:
        i += 1
        records_with_embedding = create_vector_embedding_with_bedrock(record['question'], index_name, bedrock_client)
        print(f"Embedding for record {i} created")
        records_with_embedding['sql'] = record['sql']
        records_with_embedding['profile'] = record.get('profile', 'default')
        all_json_records.append(records_with_embedding)
        if i % 500 == 0 or i == len(all_records):
            # Bulk put all records to OpenSearch
            success, failed = opensearch.put_bulk_in_opensearch(all_json_records, opensearch_client)
            all_json_records = []
            print(f"Documents saved {success}, documents failed to save {failed}")

    print("Finished creating records using Amazon Bedrock Titan text embedding")


if __name__ == "__main__":
    index_to_opensearch()