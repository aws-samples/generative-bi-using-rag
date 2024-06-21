import json
from dotenv import load_dotenv
import os
import boto3
import logging

from nlq.business.vector_store import VectorStore
from utils.opensearch import get_opensearch_cluster_client, opensearch_index_init
from utils.env_var import opensearch_info

logger = logging.getLogger(__name__)

load_dotenv()

SAGEMAKER_ENDPOINT_EMBEDDING = os.getenv('SAGEMAKER_ENDPOINT_EMBEDDING', '')

BEDROCK_REGION = os.getenv('BEDROCK_REGION')



def index_to_opensearch():

    opensearch_client = get_opensearch_cluster_client(opensearch_info["domain"], opensearch_info["host"], opensearch_info["port"],
                                                      opensearch_info["username"], opensearch_info["password"], opensearch_info["region"])

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

    def create_vector_embedding_with_sagemaker(text, index_name, sagemaker_client):
        model_kwargs = {}
        model_kwargs["batch_size"] = 12
        model_kwargs["max_length"] = 512
        model_kwargs["return_type"] = "dense"

        response_model = sagemaker_client.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT_EMBEDDING,
            Body=json.dumps({"inputs": [text], **model_kwargs}),
            ContentType="application/json",
        )
        # 中文instruction => 为这个句子生成表示以用于检索相关文章：
        json_str = response_model["Body"].read().decode("utf8")
        json_obj = json.loads(json_str)
        embeddings = json_obj["sentence_embeddings"]
        return {"_index": index_name, "text": text, "vector_field": embeddings["dense_vecs"][0]}

    def get_sagemaker_client():
        sagemaker_client = boto3.client("sagemaker-runtime")
        return sagemaker_client

    # Initialize
    if SAGEMAKER_ENDPOINT_EMBEDDING:
        dimension = 1024
        sagemaker_client = get_sagemaker_client()
    else:
        dimension = 1536
        bedrock_client = get_bedrock_client(BEDROCK_REGION)

    opensearch_index_flag = opensearch_index_init()
    if not opensearch_index_flag:
        logger.info("OpenSearch Index Create Fail")
    else:
        current_profile = "entity_insert_test"
        entity = "环比"
        comment = "环比增长率是指本期和上期相比较的增长率，计算公式为：环比增长率 =（本期数－上期数）/ 上期数 ×100%"
        VectorStore.add_entity_sample(current_profile, entity, comment)


if __name__ == "__main__":
    index_to_opensearch()