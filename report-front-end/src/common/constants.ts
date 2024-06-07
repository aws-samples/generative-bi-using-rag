export const CHATBOT_NAME = "GenBI Chatbot";

export const DEFAULT_QUERY_CONFIG = {
  selectedLLM: "anthropic.claude-3-sonnet-20240229-v1:0",
  selectedDataPro: "shopping-demo",
  intentChecked: true,
  complexChecked: true,
  answerInsightChecked: false,
  modelSuggestChecked: false,
  temperature: 0.01,
  topP: 0.999,
  topK: 250,
  maxLength: 2048,
};

export const LOCALSTORAGE_KEY = "__GEN_BI_STORE_INFO__";

export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL?.endsWith("/")
  ? import.meta.env.VITE_BACKEND_URL
  : import.meta.env.VITE_BACKEND_URL + "/";

export const APP_TITLE = import.meta.env.VITE_TITLE;

export const APP_LOGO = import.meta.env.VITE_LOGO || '';

export const APP_RIGHT_LOGO = import.meta.env.VITE_RIGHT_LOGO || '';

export const SQL_DISPLAY = import.meta.env.VITE_SQL_DISPLAY;

export const COGNITO_REGION = import.meta.env.VITE_COGNITO_REGION;

export const COGNITO_USER_POOL_ID = import.meta.env.VITE_COGNITO_USER_POOL_ID;

export const COGNITO_USER_POOL_WEB_CLIENT_ID = import.meta.env.VITE_COGNITO_USER_POOL_WEB_CLIENT_ID;