from enum import Enum, auto


class QueryState(Enum):
    INITIAL = auto()
    ENTITY_RETRIEVAL = auto()
    QA_RETRIEVAL = auto()
    SQL_GENERATION = auto()
    INTENT_RECOGNITION = auto()
    SEARCH_INTENT = auto()
    AGENT_SEARCH = auto()
    REJECT_INTENT = auto()
    KNOWLEDGE_SEARCH = auto()
    EXECUTE_QUERY = auto()
    ANALYZE_DATA = auto()
    AGENT_TASK = auto()
    AGENT_DATA_SUMMARY = auto()
    ASK_ENTITY_SELECT = auto()
    ASK_QUERY_REWRITE = auto()
    ERROR = auto()
    COMPLETE = auto()