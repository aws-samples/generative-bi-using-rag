export interface ChatInputState {
  value: string;
}

export enum ChatBotMessageType {
  AI = "AI",
  Human = "human",
}

export type ChatBotHistoryItem =
  | {
      type: ChatBotMessageType.Human;
      content: string;
    }
  | {
      type: ChatBotMessageType.AI;
      content: ChatBotAnswerItem;
    };

export interface ChatBotMessageItem {
  session_id: string;
  user_id: string;
  content_type: string;
  content: StatusMessageItem;
}

export interface StatusMessageItem {
  status: string;
  text: string;
}

export enum QUERY_INTENT {
  ask_in_reply = "ask_in_reply",
  reject_search = "reject_search",
  normal_search = "normal_search",
  agent_search = "agent_search",
  knowledge_search = "knowledge_search",
  entity_select = "entity_select",
}

export interface ChatBotAnswerItem {
  query: string;
  // LLM rewrites the query
  query_rewrite: string;
  query_intent: QUERY_INTENT;
  knowledge_search_result: KnowledgeSearchResult;
  ask_rewrite_result: AskRewriteResult;
  sql_search_result: SQLSearchResult;
  agent_search_result: AgentSearchResult;
  suggested_question: string[];
  error_log: Record<string, string>;
  ask_entity_select: {
    entity_retrieval: unknown[];
    entity_select_info: Record<string, Array<IEntityItem>>;
  };
}

export type IEntityItem = { text: string; id: string; [key: string]: string };

export enum FeedBackType {
  UPVOTE = "upvote",
  DOWNVOTE = "downvote",
}

export interface FeedBackItem {
  feedback_type: FeedBackType;
  data_profiles: string;
  query: string;
  query_intent: string;
  query_answer: string;
  // downvote feedback only ⬇️
  session_id?: string;
  user_id?: string;
  error_description?: string;
  error_categories?: string;
  correct_sql_reference?: string;
}

export interface SessionItem {
  user_id: string;
  profile_name: string;
}

export interface HistoryItem {
  user_id: string;
  session_id: string;
  profile_name: string;
}

export interface AskRewriteResult {
  query_rewrite: string;
}

export interface KnowledgeSearchResult {
  knowledge_response: string;
}

export interface SQLSearchResult {
  // SQL string
  sql: string;
  // table data
  sql_data: any[][];
  // chart data
  sql_data_chart: SQLDataChart[];
  // chart type: default - "Table"
  data_show_type: "bar" | "line" | "table" | "pie";
  // Desc of SQL ⬇️
  sql_gen_process: string;
  // Answer with insights ⬇️
  data_analyse: string;
}

export interface SQLDataChart {
  chart_type: string;
  chart_data: any[][];
}

export interface AgentSQLSearchResult {
  sub_task_query: string;
  sql_search_result: SQLSearchResult;

  // 'sub_search_task': any[],
  // 'agent_sql_search_result': any[],
  // 'agent_summary': string
}

export interface AgentSearchResult {
  agent_sql_search_result: AgentSQLSearchResult[];
  agent_summary: string;
}
