export interface ChatBotConfiguration {
  streaming: boolean;
  showMetadata: boolean;
  maxTokens: number;
  temperature: number;
  topP: number;
}

export interface ChatInputState {
  value: string;
}

export interface ChatBotHistoryItem {
  query: string,
  query_intent: string,
  knowledge_search_result: { knowledge_response: string },
  sql_search_result: SQLSearchResult,
  agent_search_result: AgentSearchResult,
  suggested_question: string[]
}

export interface SQLSearchResult {
  sql: string;
  sql_data: any[][];
  data_show_type: string;
  sql_gen_process: string;
  data_analyse: string;
}

export interface AgentSQLSearchResult {
  sub_search_task: string;
  sql_search_result: SQLSearchResult;
}

export interface AgentSearchResult {
  agent_sql_search_result: AgentSQLSearchResult[];
  agent_summary: string;
}
