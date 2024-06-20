import json
from utils import opensearch
from opensearchpy import OpenSearch
from dotenv import load_dotenv
import os
import boto3
import sys
import logging

class OpenSearchDeploy():
    def __init__(self):
        load_dotenv()

        self.SAGEMAKER_ENDPOINT_EMBEDDING = os.getenv('SAGEMAKER_ENDPOINT_EMBEDDING', '')

        self.AOS_HOST = os.getenv('AOS_HOST', '')
        self.AOS_PORT = os.getenv('AOS_PORT', 9200)
        self.AOS_USER = os.getenv('AOS_USER', 'admin')
        self.AOS_PASSWORD = os.getenv('AOS_PASSWORD', 'admin')
        self.AOS_DOMAIN = os.getenv('AOS_DOMAIN', 'llm-data-analytics')
        self.AOS_REGION = os.getenv('AOS_REGION')
        self.AOS_INDEX = os.getenv('AOS_INDEX', 'uba')
        self.AOS_INDEX_NER = os.getenv('AOS_INDEX_NER', 'uba_ner')
        self.AOS_INDEX_AGENT = os.getenv('AOS_INDEX_AGENT', 'uba_agent')
        self.AOS_TYPE = os.getenv('AOS_TYPE', 'uba')
        self.BEDROCK_REGION = os.getenv('BEDROCK_REGION')

        self.REGION_NAME = self.AOS_REGION
        self.early_stop_record_count = 100
        self.index_name = self.AOS_INDEX
        self.index_name_ner = self.AOS_INDEX_NER
        self.index_name_agent = self.AOS_INDEX_AGENT
        self.opensearch_user = self.AOS_USER
        self.opensearch_password = self.AOS_PASSWORD
        self.domain = self.AOS_DOMAIN

        if self.SAGEMAKER_ENDPOINT_EMBEDDING:
            self.dimension = 1024            
        else:
            self.dimension = 1536

        self.logger = logging.getLogger(__name__)
        
        # create_index = True
        # if len(sys.argv) == 1:
        #     self.logger.info(f'found {len(bulk_questions)} questions in default collection')
        # elif 2 <= len(sys.argv) < 4:
        #     bulk_questions = custom_bulk_questions[sys.argv[1]]
        #     self.logger.info(f'found {len(bulk_questions)} questions in {sys.argv[1]} collection')
        #     if len(sys.argv) == 3 and sys.argv[2] == 'false':
        #         create_index = False
        # else:
        #     self.logger.info('Usage: python3 opensearch_deploy.py <collection_name> <create_index:bool>')
        #     self.logger.info('       create_index: true (default) or false')
        #     return

        if self.AOS_HOST == '':
            self.logger.info("AOS Host not provided")
            return 
        else:
            auth = (self.opensearch_user, self.opensearch_password)
            host = self.AOS_HOST
            port = self.AOS_PORT
            self.opensearch_client = OpenSearch(
                hosts=[{'host': host, 'port': port}],
                http_compress=True,
                http_auth=auth,
                use_ssl=True,
                verify_certs=False,
                ssl_assert_hostname=False,
                ssl_show_warn=False
            )


    def create_vector_embedding_with_bedrock(self, text, index_name, bedrock_client):
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

    def get_bedrock_client(self, region):
        bedrock_client = boto3.client("bedrock-runtime", region_name=region)
        return bedrock_client

    def create_vector_embedding_with_sagemaker(self, text, index_name, sagemaker_client):
        model_kwargs = {}
        model_kwargs["batch_size"] = 12
        model_kwargs["max_length"] = 512
        model_kwargs["return_type"] = "dense"

        response_model = sagemaker_client.invoke_endpoint(
            EndpointName=self.SAGEMAKER_ENDPOINT_EMBEDDING,
            Body=json.dumps({"inputs": [text], **model_kwargs}),
            ContentType="application/json",
        )

        json_str = response_model["Body"].read().decode("utf8")
        json_obj = json.loads(json_str)
        embeddings = json_obj["sentence_embeddings"]
        return {"_index": index_name, "text": text, "vector_field": embeddings["dense_vecs"][0]}

    def get_sagemaker_client(self):
            sagemaker_client = boto3.client("sagemaker-runtime")
            return sagemaker_client

    def create_indexes(self):
        exists = opensearch.check_opensearch_index(self.opensearch_client, self.index_name)
        if not exists:
            self.logger.info("Creating OpenSearch index")
            success = opensearch.create_index(self.opensearch_client, self.index_name)
            if success:
                self.logger.info("Creating OpenSearch index mapping")
                success = opensearch.create_index_mapping(self.opensearch_client, self.index_name, 1024)
                self.logger.info(f"OpenSearch Index mapping created")
        else:
            self.logger.info("Index already exists. Exit with 0 now.")

        exists_ner = opensearch.check_opensearch_index(self.opensearch_client, self.index_name_ner)
        if not exists_ner:
            self.logger.info("Creating OpenSearch Ner index")
            success = opensearch.create_index(self.opensearch_client, self.index_name_ner)
            if success:
                self.logger.info("Creating OpenSearch Ner Index mapping")
                success = opensearch.create_index_mapping(self.opensearch_client, self.index_name_ner, self.dimension)
                self.logger.info(f"OpenSearch Ner Index mapping created")
        else:
            self.logger.info("OpenSearch Ner index already exists. Exit with 0 now.")

        exists_agent = opensearch.check_opensearch_index(self.opensearch_client, self.index_name_agent)
        if not exists_agent:
            self.logger.info("Create OpenSearch Agent index")
            success = opensearch.create_index(self.opensearch_client, self.index_name_agent)
            if success:
                self.logger.info("Creating OpenSearch Agent Index mapping")
                success = opensearch.create_index_mapping(self.opensearch_client, self.index_name_agent, self.dimension)
                self.logger.info(f"OpenSearch Agent Index mapping created")
        else: 
            self.logger.info("OpenSearch Agent index already exists. Exit with 0 now.")
        return exists
                
    def bulk_insert(self, bulk_questions):
        if self.SAGEMAKER_ENDPOINT_EMBEDDING:
            sagemaker_client = self.get_sagemaker_client()
        else:
            bedrock_client = self.get_bedrock_client(self.BEDROCK_REGION)

        all_records = bulk_questions

        all_json_records = []
        self.logger.info(f"Creating embeddings for records")

        i = 0
        for record in all_records:
            i += 1
            if self.SAGEMAKER_ENDPOINT_EMBEDDING:
                records_with_embedding = self.create_vector_embedding_with_sagemaker(record['question'], self.index_name, sagemaker_client)
            else:
                records_with_embedding = self.create_vector_embedding_with_bedrock(record['question'], self.index_name, bedrock_client)
            self.logger.info(f"Embedding for record {i} created")
            records_with_embedding['sql'] = record['sql']
            records_with_embedding['profile'] = record.get('profile', 'default')
            all_json_records.append(records_with_embedding)
            if i % 500 == 0 or i == len(all_records):
                success, failed = opensearch.put_bulk_in_opensearch(all_json_records, self.opensearch_client)
                all_json_records = []
                self.logger.info(f"Documents saved {success}, documents failed to save {failed}")

        self.logger.info("Finished creating records using Amazon Bedrock Titan text embedding")
        
if __name__ == "__main__":
    from deployment.default_index_data import bulk_questions
    opensearch_deploy = OpenSearchDeploy()

    exists = opensearch_deploy.create_indexes()
    if not exists:
        opensearch_deploy.bulk_insert(bulk_questions)