import boto3
import json
from nlq.data_access.opensearch import OpenSearchDao
from utils.env_var import BEDROCK_REGION, AOS_HOST, AOS_PORT, AOS_USER, AOS_PASSWORD, opensearch_info, embedding_info
from utils.env_var import bedrock_ak_sk_info
from utils.llm import invoke_model_sagemaker_endpoint
from utils.logging import getLogger

logger = getLogger()


class VectorStore:
    opensearch_dao = OpenSearchDao(AOS_HOST, AOS_PORT, AOS_USER, AOS_PASSWORD)
    if len(bedrock_ak_sk_info) == 0:
        bedrock_client = boto3.client(service_name='bedrock-runtime', region_name=BEDROCK_REGION)
    else:
        bedrock_client = boto3.client(
            service_name='bedrock-runtime', region_name=BEDROCK_REGION,
            aws_access_key_id=bedrock_ak_sk_info['access_key_id'],
            aws_secret_access_key=bedrock_ak_sk_info['secret_access_key'])

    @classmethod
    def get_all_samples(cls, profile_name):
        logger.info(f'get all samples for {profile_name}...')
        samples = cls.opensearch_dao.retrieve_samples(opensearch_info['sql_index'], profile_name)

        sample_list = []
        for sample in samples:
            sample_list.append({
                'id': sample['_id'],
                'text': sample['_source']['text'],
                'sql': sample['_source']['sql']
            })

        return sample_list

    @classmethod
    def get_all_entity_samples(cls, profile_name):
        logger.info(f'get all samples for {profile_name}...')
        samples = cls.opensearch_dao.retrieve_entity_samples(opensearch_info['ner_index'], profile_name)

        sample_list = []
        if samples is None:
            return sample_list

        for sample in samples:
            sample_list.append({
                'id': sample['_id'],
                'entity': sample['_source']['entity'],
                'comment': sample['_source']['comment'],
                'entity_type': sample['_source']['entity_type'],
                'entity_table_info': sample['_source']['entity_table_info']
            })

        return sample_list

    @classmethod
    def get_all_agent_cot_samples(cls, profile_name):
        logger.info(f'get all agent cot samples for {profile_name}...')
        samples = cls.opensearch_dao.retrieve_agent_cot_samples(opensearch_info['agent_index'], profile_name)

        sample_list = []
        if samples is None:
            return sample_list

        for sample in samples:
            sample_list.append({
                'id': sample['_id'],
                'query': sample['_source']['query'],
                'comment': sample['_source']['comment']
            })

        return sample_list

    @classmethod
    def add_sample(cls, profile_name, question, answer):
        logger.info(f'add sample question: {question} to profile {profile_name}')
        embedding = cls.create_vector_embedding(question)
        has_same_sample = cls.search_same_query(profile_name, 1, opensearch_info['sql_index'], embedding)
        if has_same_sample:
            logger.info(f'delete sample sample entity: {question} to profile {profile_name}')
        if cls.opensearch_dao.add_sample(opensearch_info['sql_index'], profile_name, question, answer, embedding):
            logger.info('Sample added')

    @classmethod
    def add_entity_sample(cls, profile_name, entity, comment, entity_type="metrics"):
        logger.info(f'add sample entity: {entity} to profile {profile_name}')
        embedding = cls.create_vector_embedding(entity)
        has_same_sample = cls.search_same_query(profile_name, 5, opensearch_info['ner_index'], embedding)
        if has_same_sample:
            logger.info(f'delete sample sample entity: {entity} to profile {profile_name}')
        if cls.opensearch_dao.add_entity_sample(opensearch_info['ner_index'], profile_name, entity, comment, embedding,
                                                entity_type):
            logger.info('Sample added')

    @classmethod
    def add_entity_dimension_batch_sample(cls, profile_name, entity, comment, entity_type="dimension", entity_info=[]):
        entity_value_set = set()
        for entity_table in entity_info:
            entity_value_set.add(
                entity_table["table_name"] + "#" + entity_table["column_name"] + "#" + entity_table["value"])
        logger.info(f'add sample entity: {entity} to profile {profile_name}')
        embedding = cls.create_vector_embedding(entity)
        same_dimension_value = cls.search_same_dimension_entity(profile_name, 5, opensearch_info['ner_index'],
                                                                embedding)
        if len(same_dimension_value) > 0:
            for dimension_value in same_dimension_value:
                entity_special_id = dimension_value["table_name"] + "#" + dimension_value["column_name"] + "#" + \
                                    dimension_value["value"]
                if entity_special_id not in entity_value_set:
                    entity_info.append(dimension_value)
        logger.info("entity_table_info: " + str(entity_info))
        if cls.opensearch_dao.add_entity_sample(opensearch_info['ner_index'], profile_name, entity, comment, embedding,
                                                entity_type, entity_info):
            logger.info('Sample added')

    @classmethod
    def add_agent_cot_sample(cls, profile_name, entity, comment):
        logger.info(f'add agent sample query: {entity} to profile {profile_name}')
        embedding = cls.create_vector_embedding(entity)
        has_same_sample = cls.search_same_query(profile_name, 1, opensearch_info['agent_index'], embedding)
        if has_same_sample:
            logger.info(f'delete agent sample sample query: {entity} to profile {profile_name}')
        if cls.opensearch_dao.add_agent_cot_sample(opensearch_info['agent_index'], profile_name, entity, comment,
                                                   embedding):
            logger.info('Sample added')

    @classmethod
    def create_vector_embedding(cls, text):
        model_name = embedding_info["embedding_name"]
        if embedding_info["embedding_platform"] == "bedrock":
            return cls.create_vector_embedding_with_bedrock(text, model_name)
        else:
            return cls.create_vector_embedding_with_sagemaker(text, model_name)

    @classmethod
    def create_vector_embedding_with_bedrock(cls, text, model_name):
        payload = {"inputText": f"{text}"}
        body = json.dumps(payload)
        modelId = model_name
        accept = "application/json"
        contentType = "application/json"

        response = cls.bedrock_client.invoke_model(
            body=body, modelId=modelId, accept=accept, contentType=contentType
        )
        response_body = json.loads(response.get("body").read())

        embedding = response_body.get("embedding")

        return embedding

    @classmethod
    def create_vector_embedding_with_sagemaker(cls, text, model_name):
        try:
            body = json.dumps(
                {
                    "inputs": text,
                    "is_query": True
                }
            )
            response = invoke_model_sagemaker_endpoint(model_name, body, model_type="embedding")
            embeddings = response[0]
            return embeddings
        except Exception as e:
            logger.error(f'create_vector_embedding_with_sagemaker is error {e}')

    @classmethod
    def delete_sample(cls, profile_name, doc_id):
        logger.info(f'delete sample question id: {doc_id} from profile {profile_name}')
        ret = cls.opensearch_dao.delete_sample(opensearch_info['sql_index'], profile_name, doc_id)
        print(ret)

    @classmethod
    def delete_entity_sample(cls, profile_name, doc_id):
        logger.info(f'delete sample question id: {doc_id} from profile {profile_name}')
        ret = cls.opensearch_dao.delete_sample(opensearch_info['ner_index'], profile_name, doc_id)
        print(ret)

    @classmethod
    def delete_agent_cot_sample(cls, profile_name, doc_id):
        logger.info(f'delete sample question id: {doc_id} from profile {profile_name}')
        ret = cls.opensearch_dao.delete_sample(opensearch_info['agent_index'], profile_name, doc_id)
        print(ret)

    @classmethod
    def search_sample(cls, profile_name, top_k, index_name, query):
        logger.info(f'search sample question: {query}  {index_name} from profile {profile_name}')
        sample_list = cls.opensearch_dao.search_sample(profile_name, top_k, index_name, query)
        return sample_list

    @classmethod
    def search_sample_with_embedding(cls, profile_name, top_k, index_name, query_embedding):
        sample_list = cls.opensearch_dao.search_sample_with_embedding(profile_name, top_k, index_name, query_embedding)
        return sample_list

    @classmethod
    def search_same_query(cls, profile_name, top_k, index_name, embedding):
        search_res = cls.search_sample_with_embedding(profile_name, top_k, index_name, embedding)
        if len(search_res) > 0:
            similarity_sample = search_res[0]
            similarity_score = similarity_sample["_score"]
            similarity_id = similarity_sample['_id']
            if similarity_score == 1.0:
                if index_name == opensearch_info['sql_index']:
                    cls.delete_sample(profile_name, similarity_id)
                    return True
                elif index_name == opensearch_info['ner_index']:
                    cls.delete_entity_sample(profile_name, similarity_id)
                    return True
                elif index_name == opensearch_info['agent_index']:
                    cls.delete_agent_cot_sample(profile_name, similarity_id)
                    return True
                else:
                    return False
        return False

    @classmethod
    def search_same_dimension_entity(cls, profile_name, top_k, index_name, embedding):
        search_res = cls.search_sample_with_embedding(profile_name, top_k, index_name, embedding)
        same_dimension_value = []
        if len(search_res) > 0:
            for i in range(len(search_res)):
                similarity_sample = search_res[i]
                similarity_score = similarity_sample["_score"]
                if similarity_score == 1.0:
                    if similarity_sample["_source"]["entity_type"] == "dimension":
                        entity_table_info = similarity_sample["_source"]["entity_table_info"]
                        for each in entity_table_info:
                            same_dimension_value.append(each)
                    sample_id = similarity_sample['_id']
                    VectorStore.delete_entity_sample(profile_name, sample_id)
        return same_dimension_value
