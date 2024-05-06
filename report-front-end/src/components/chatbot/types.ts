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

export enum ChatBotMessageType {
  AI = "ai",
  Human = "human",
}

export interface ChatBotHistoryItem {
  type: ChatBotMessageType;
  content: string;
}
