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
  sql_search_result: { sql: string, sql_data: any[][], data_show_type: string, sql_gen_process: string, data_analyse: string },
  agent_search_result: { agent_sql_search_result: any[], agent_summary: string },
  suggested_question: string[]
}
