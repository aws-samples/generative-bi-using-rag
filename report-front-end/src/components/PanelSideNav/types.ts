import { ChatBotHistoryItem } from "../Chat/types";

export interface Session {
  session_id: string;
  title: string;
  messages: ChatBotHistoryItem[];
}
