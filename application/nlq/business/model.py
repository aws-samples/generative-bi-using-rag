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
                'model_type': model.model_type,
                'prompt_template': model.prompt_template,
                'extra_params': model.extra_params 
            }

        return model_map

    @classmethod
    def add_model(cls, model_id, model_type, prompt_template, extra_params):
        entity = ModelConfigEntity(model_id, model_type, prompt_template, extra_params)
        cls.model_config_dao.add(entity)
        logger.info(f"Model {model_id} added")

    @classmethod
    def get_model_by_id(cls, model_id):
        return cls.model_config_dao.get_by_id(model_id)

    @classmethod
    def update_model(cls, model_id, model_type, prompt_template, extra_params):
        all_models = ModelManagement.get_all_models_with_info()
        entity = ModelConfigEntity(model_id, model_type, prompt_template, extra_params)
        cls.model_config_dao.update(entity)
        logger.info(f"Model {model_id} updated")

    @classmethod
    def delete_model(cls, model_id):
        cls.model_config_dao.delete(model_id)
        logger.info(f"Model {model_id} updated")

