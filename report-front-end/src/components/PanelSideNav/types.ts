import { ChatBotHistoryItem } from "../SectionChat/types";

export interface Session {
  session_id: string;
  title: string;
  messages: ChatBotHistoryItem[];
}
