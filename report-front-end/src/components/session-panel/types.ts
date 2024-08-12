import { ChatBotHistoryItem } from "../chatbot-panel/types";

export interface Session {
  session_id: string;
  title: string;
  messages: ChatBotHistoryItem[];
}