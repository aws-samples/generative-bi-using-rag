from dataclasses import dataclass


@dataclass
class SearchTextSqlResult:
    search_query: str
    entity_slot_retrieve: list
    retrieve_result: list
    response: str
    sql: str

@dataclass
class SearchTextJsonResult:
    search_query: str
    entity_slot_retrieve: list
    retrieve_result: list
    response: str
    json: str
    process_think: str
