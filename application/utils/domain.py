from dataclasses import dataclass
from typing import Any


@dataclass
class SearchTextSqlResult:
    search_query: str
    entity_slot_retrieve: list
    retrieve_result: list
    response: str
    sql: str
    '''Origin sql before post processing'''
    original_sql: str = ''


@dataclass
class ModelResponse:
    response: str = ''
    text: str = ''
    token_info: dict[str, Any] = None
