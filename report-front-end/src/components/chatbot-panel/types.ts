export interface ChatInputState {
  value: string;
}

export enum ChatBotMessageType {
  AI = "AI",
  Human = "human",
}

export interface ChatBotHistoryItem {
  type: ChatBotMessageType;
  content: string | ChatBotAnswerItem;
}

export interface ChatBotMessageItem {
  session_id: string,
  user_id: string,
  content_type: string,
  content: StatusMessageItem
}

export interface StatusMessageItem {
  status: string;
  text: string;
}

export interface ChatBotAnswerItem {
  query: string,
  query_intent: string,
  knowledge_search_result: KnowledgeSearchResult,
  ask_rewrite_result: AskRewriteResult,
  sql_search_result: SQLSearchResult,
  agent_search_result: AgentSearchResult,
  suggested_question: string[]
}

export enum FeedBackType {
  UPVOTE = "upvote",
  DOWNVOTE = "downvote",
}

export interface FeedBackItem {
  feedback_type: FeedBackType,
  data_profiles: string,
  query: string,
  query_intent: string,
  query_answer: string,
}

export interface SessionItem {
  user_id: string,
  profile_name: string,
}

export interface HistoryItem {
  user_id: string,
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
  sql: string;
  sql_data: any[][];
  sql_data_chart: SQLDataChart[];
  data_show_type: string;
  sql_gen_process: string;
  data_analyse: string;
}

export interface SQLDataChart {
  chart_type: string;
  chart_data: any[][];
}

export interface AgentSQLSearchResult {
  sub_task_query: string;
  sql_search_result: SQLSearchResult;
}

export interface AgentSearchResult {
  agent_sql_search_result: AgentSQLSearchResult[];
  agent_summary: string;
}
