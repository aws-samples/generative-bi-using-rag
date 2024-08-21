from dataclasses import dataclass


@dataclass
class SearchTextSqlResult:
    search_query: str
    entity_slot_retrieve: list
    retrieve_result: list
    response: str
    sql: str
    '''Origin sql before post processing'''
    original_sql: str = ''
