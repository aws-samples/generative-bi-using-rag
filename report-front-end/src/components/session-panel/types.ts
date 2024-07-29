import { ChatBotHistoryItem } from "../chatbot-panel/types";

export interface Session {
  session_id: string;
  messages: ChatBotHistoryItem[];
}