export interface ChatInputState {
  value: string;
}

export enum ChatBotMessageType {
  AI = "ai",
  Human = "human",
}

/*export interface ChatBotHistoryItem {
  type: ChatBotMessageType;
  content: any;
}*/

export interface ChatBotHistoryItem {
  query: string,
  query_intent: string,
  knowledge_search_result: KnowledgeSearchResult,
  sql_search_result: SQLSearchResult,
  agent_search_result: AgentSearchResult,
  suggested_question: string[]
}

export interface KnowledgeSearchResult {
  knowledge_response: string;
}

export interface SQLSearchResult {
  sql: string;
  sql_data: any[][];
  data_show_type: string;
  sql_gen_process: string;
  data_analyse: string;
}

export interface AgentSQLSearchResult {
  sub_task_query: string;
  sql_search_result: SQLSearchResult;
}

export interface AgentSearchResult {
  agent_sql_search_result: AgentSQLSearchResult[];
  agent_summary: string;
}
