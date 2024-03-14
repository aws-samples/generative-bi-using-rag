from loguru import logger
import os
import boto3
import json
from nlq.data_access.opensearch import OpenSearchDao
from utils.env_var import BEDROCK_REGION, AOS_HOST, AOS_PORT, AOS_USER, AOS_PASSWORD


class VectorStore:
    opensearch_dao = OpenSearchDao(AOS_HOST, AOS_PORT, AOS_USER, AOS_PASSWORD)
    bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

    @classmethod
    def get_all_samples(cls, profile_name):
        logger.info(f'get all samples for {profile_name}...')
        samples = cls.opensearch_dao.retrieve_samples('uba', profile_name)

        sample_list = []
        for sample in samples:
            sample_list.append({
                'id': sample['_id'],
                'text': sample['_source']['text'],
                'sql': sample['_source']['sql']
            })

        return sample_list

    @classmethod
    def add_sample(cls, profile_name, question, answer):
        logger.info(f'add sample question: {question} to profile {profile_name}')
        embedding = cls.create_vector_embedding_with_bedrock(question)
        if cls.opensearch_dao.add_sample('uba', profile_name, question, answer, embedding):
            logger.info('Sample added')

    @classmethod
    def create_vector_embedding_with_bedrock(cls, text):
        payload = {"inputText": f"{text}"}
        body = json.dumps(payload)
        modelId = "amazon.titan-embed-text-v1"
        accept = "application/json"
        contentType = "application/json"

        response = cls.bedrock_client.invoke_model(
            body=body, modelId=modelId, accept=accept, contentType=contentType
        )
        response_body = json.loads(response.get("body").read())

        embedding = response_body.get("embedding")

        return embedding

    @classmethod
    def delete_sample(cls, profile_name, doc_id):
        logger.info(f'delete sample question id: {doc_id} from profile {profile_name}')
        ret = cls.opensearch_dao.delete_sample('uba', profile_name, doc_id)
        print(ret)