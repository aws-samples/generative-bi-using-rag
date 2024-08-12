from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ProcessingContext:
    search_box: str
    query_rewrite: str
    session_id: str
    user_id: str
    selected_profile: str
    database_profile: Dict[str, Any]
    model_type: str
    use_rag_flag: bool
    intent_ner_recognition_flag: bool
    agent_cot_flag: bool
    explain_gen_process_flag: bool
    visualize_results_flag: bool
    data_with_analyse: bool
    gen_suggested_question_flag: bool
    auto_correction_flag: bool
    context_window: int
    entity_same_name_select: Dict[str, Any]
    user_query_history: List[str]
    opensearch_info = Dict[str, Any]
    previous_state: str = "INITIAL"


@dataclass
class LogContext:
    session_id: str
    user_id: str
    search_box: str
    query_rewrite: str
    query_intent: str
    current_state: str
    knowledge_search_result: Any
    sql_search_result: Any
    agent_search_result: Any
    ask_rewrite_result: Any
    ask_entity_result : str
    suggested_question: list[str]


