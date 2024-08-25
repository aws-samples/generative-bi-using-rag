import logging
from nlq.data_access.dynamo_model import ModelConfigDao, ModelConfigEntity

logger = logging.getLogger(__name__)


class ModelManagement:
    model_config_dao = ModelConfigDao()

    @classmethod
    def get_all_models(cls):
        logger.info('get all models...')
        return [conn.model_id for conn in cls.model_config_dao.get_model_list()]

    @classmethod
    def get_all_models_with_info(cls):
        logger.info('get all models with info...')
        model_list = cls.model_config_dao.get_model_list()
        model_map = {}
        for model in model_list:
            model_map[model.model_id] = {
                'model_region': model.model_region,
                'prompt_template': model.prompt_template,
                'input_payload': model.input_payload,
                'output_format': model.output_format
            }

        return model_map

    @classmethod
    def add_model(cls, model_id, model_region, prompt_template, input_payload, output_format):
        entity = ModelConfigEntity(model_id, model_region, prompt_template, input_payload, output_format)
        cls.model_config_dao.add(entity)
        logger.info(f"Model {model_id} added")

    @classmethod
    def get_model_by_id(cls, model_id):
        return cls.model_config_dao.get_by_id(model_id)

    @classmethod
    def update_model(cls, model_id, model_region, prompt_template, input_payload, output_format):
        entity = ModelConfigEntity(model_id, model_region, prompt_template, input_payload, output_format)
        cls.model_config_dao.update(entity)
        logger.info(f"Model {model_id} updated")

    @classmethod
    def delete_model(cls, model_id):
        cls.model_config_dao.delete(model_id)
        logger.info(f"Model {model_id} updated")
