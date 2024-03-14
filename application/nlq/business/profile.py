from loguru import logger
from nlq.data_access.dynamo_profile import ProfileConfigDao, ProfileConfigEntity


class ProfileManagement:
    profile_config_dao = ProfileConfigDao()

    @classmethod
    def get_all_profiles(cls):
        logger.info('get all profiles...')
        return [conn.profile_name for conn in cls.profile_config_dao.get_profile_list()]

    @classmethod
    def get_all_profiles_with_info(cls):
        logger.info('get all profiles with info...')
        profile_list = cls.profile_config_dao.get_profile_list()
        profile_map = {}
        for profile in profile_list:
            profile_map[profile.profile_name] = {
                'db_url': '',
                'conn_name': profile.conn_name,
                'tables_info': profile.tables_info,
                'hints': '',
                'search_samples': [],
                'comments':  profile.comments,
            }

        return profile_map

    @classmethod
    def add_profile(cls, profile_name, conn_name, schemas, tables, comment):
        entity = ProfileConfigEntity(profile_name, conn_name, schemas, tables, comment)
        cls.profile_config_dao.add(entity)
        logger.info(f"Profile {profile_name} added")

    @classmethod
    def get_profile_by_name(cls, profile_name):
        return cls.profile_config_dao.get_by_name(profile_name)

    @classmethod
    def update_profile(cls, profile_name, conn_name, schemas, tables, comment, tables_info):
        entity = ProfileConfigEntity(profile_name, conn_name, schemas, tables, comment, tables_info)
        cls.profile_config_dao.update(entity)
        logger.info(f"Profile {profile_name} updated")

    @classmethod
    def delete_profile(cls, profile_name):
        cls.profile_config_dao.delete(profile_name)
        logger.info(f"Profile {profile_name} updated")

    @classmethod
    def update_table_def(cls, profile_name, tables_info, merge_before_update=False):
        if merge_before_update:
            old_profile = cls.get_profile_by_name(profile_name)
            old_tables_info = old_profile.tables_info
            if old_tables_info is not None:
                # print(old_tables_info)
                for table_name, table_info in tables_info.items():
                    # copy annotation to new table info if old table has annotation
                    if table_name in old_tables_info:
                        table_info['tbl_a'] = old_tables_info[table_name]['tbl_a']
                        table_info['col_a'] = old_tables_info[table_name]['col_a']

                logger.info('tables info merged', tables_info)

        cls.profile_config_dao.update_table_def(profile_name, tables_info)
        logger.info(f"Table definition updated")
