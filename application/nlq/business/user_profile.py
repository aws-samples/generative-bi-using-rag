import logging
from nlq.data_access.dynamo_user_profile import UserProfileConfigDao, UserProfileConfigEntity

logger = logging.getLogger(__name__)

class UserProfileManagement:
    user_profile_config_dao = UserProfileConfigDao()

    @classmethod
    def get_all_user_profiles(cls):
        logger.info('get all profiles...')
        logger.info(cls.user_profile_config_dao.get_user_profile_list())
        logger.info('=' * 20)
        return [item.user_id for item in cls.user_profile_config_dao.get_user_profile_list()]

    @classmethod
    def get_all_user_profiles_with_info(cls):
        logger.info('get all user_profiles with info...')
        get_user_profile_list = cls.user_profile_config_dao.get_user_profile_list()
        user_profile_map = {}
        for user_profile in get_user_profile_list:
            user_profile_map[user_profile.user_id] = {
                'profile_name_list': user_profile.profile_name_list
            }
        return user_profile_map

    @classmethod
    def add_user_profile(cls, user_id, profile_name):
        print(user_id)
        print(profile_name)
        entity = UserProfileConfigEntity(user_id, profile_name)
        print(entity)
        cls.user_profile_config_dao.add(entity)
        logger.info(f"User Profile {user_id} added")

    @classmethod
    def get_user_profile_by_id(cls, user_id):
        return cls.user_profile_config_dao.get_by_name(user_id)

    @classmethod
    def update_user_profile(cls, user_id, profile_name_list):
        entity = UserProfileConfigEntity(user_id,profile_name_list)
        old_user_profile_list = cls.get_user_profile_by_id(user_id)
        if old_user_profile_list:
            cls.user_profile_config_dao.update(entity)
        else:
            cls.user_profile_config_dao.add(entity)

        logger.info(f"User Profile {user_id} updated")

    @classmethod
    def delete_user_profile(cls, user_id):
        cls.user_profile_config_dao.delete(user_id)
        logger.info(f"User Profile {user_id} updated")
