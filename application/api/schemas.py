from typing import Any
from pydantic import BaseModel


class Question(BaseModel):
    keywords: str
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    use_rag: bool = True
    query_result: bool = True
    intent_ner_recognition: bool = False
    agent_cot: bool = False
    profile_name: str = "shopping_guide"
    explain_gen_process_flag: bool = False
    gen_suggested_question: bool = False


class QuestionSocket(Question):
    session_id: str


class Example(BaseModel):
    score: float
    question: str
    answer: str


class Answer(BaseModel):
    examples: list[Example]
    sql: str
    sql_explain: str
    sql_query_result: list[Any]


class Option(BaseModel):
    data_profiles: list[str]
    bedrock_model_ids: list[str]


class CustomQuestion(BaseModel):
    custom_question: list[str]