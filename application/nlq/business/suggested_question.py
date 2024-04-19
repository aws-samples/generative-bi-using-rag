import logging
from nlq.data_access.dynamo_suggested_question import SuggestedQuestionDao, SuggestedQuestionEntity
from datetime import datetime, timezone
from utils.constant import PROFILE_QUESTION_TABLE_NAME, ACTIVE_PROMPT_NAME, DEFAULT_PROMPT_NAME

logger = logging.getLogger(__name__)

class SuggestedQuestionManagement:
    sq_dao = SuggestedQuestionDao()

    @classmethod
    def get_prompt_by_name(cls, prompt_name: str):
        return cls.sq_dao.get_by_name(prompt_name)

    @classmethod
    def update_prompt(cls, prompt: str):
        current_time = datetime.now(timezone.utc)
        formatted_time = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        logger.info(f"Creation time: %s", formatted_time)
        entity = SuggestedQuestionEntity(prompt, formatted_time)
        cls.sq_dao.update(entity)
        logger.info("Prompt updated")

    @classmethod
    def reset_to_default(cls):
        response = cls.sq_dao.get_by_name(DEFAULT_PROMPT_NAME)
        logger.info(response.prompt)
        return response.prompt
