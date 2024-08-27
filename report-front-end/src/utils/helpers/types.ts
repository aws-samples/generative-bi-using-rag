export const COMMON_ALERT_TYPE = {
  Success: "success",
  Error: "error",
  Warning: "warning",
  Info: "info",
};

export enum ActionType {
  Delete = "Delete",
  UpdateUserInfo = "UpdateUserInfo",
  UpdateConfig = "UpdateConfig",
}

export type UserState = {
  userInfo: UserInfo;
  queryConfig: LLMConfigState;
};

export type UserInfo = {
  userId: string;
  displayName: string;
  loginExpiration: number;
  isLogin: boolean;
  username: string;
};

export type LLMConfigState = {
  selectedLLM: string;
  selectedDataPro: string;
  intentChecked: boolean;
  complexChecked: boolean;
  answerInsightChecked: boolean;
  contextWindow: number;
  modelSuggestChecked: boolean;
  temperature: number;
  topP: number;
  topK: number;
  maxLength: number;
};

export type UserAction = { type: ActionType; state?: any };
