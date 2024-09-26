export const CHATBOT_NAME = "GenBI Chatbot";

export const DEFAULT_USER_INFO = {
  userId: "",
  displayName: "",
  loginExpiration: +new Date() + 6000,
  isLogin: false,
  username: "anonymous",
};

export const DEFAULT_QUERY_CONFIG = {
  selectedLLM: "",
  selectedDataPro: "",
  intentChecked: true,
  complexChecked: true,
  answerInsightChecked: false,
  contextWindow: 0,
  modelSuggestChecked: false,
  temperature: 0.1,
  topP: 1,
  topK: 250,
  maxLength: 2048,
};

export const LOCALSTORAGE_KEY = "__GEN_BI_STORE_INFO__";

export enum AUTH_METHOD {
  COGNITO = "Cognito",
  OIDC = "OIDC",
  AZUREAD = "AZUREAD",
  SSO = "SSO", // Single Sign On method
}
export const LOGIN_TYPE = process.env.VITE_LOGIN_TYPE;
export const AUTH_WITH_COGNITO = LOGIN_TYPE === AUTH_METHOD.COGNITO;
export const AUTH_WITH_OIDC = LOGIN_TYPE === AUTH_METHOD.OIDC;
export const AUTH_WITH_SSO = LOGIN_TYPE === AUTH_METHOD.SSO;
export const AUTH_WITH_AZUREAD = LOGIN_TYPE === AUTH_METHOD.AZUREAD;
export const AUTH_WITH_NOTHING =
  !AUTH_WITH_COGNITO && !AUTH_WITH_OIDC && !AUTH_WITH_SSO && !AUTH_WITH_AZUREAD;

export const SSO_FED_AUTH_PROVIDER = import.meta.env.VITE_SSO_FED_AUTH_PROVIDER;
export let AZURE_AD_SCOPE = import.meta.env.VITE_AZURE_AD_SCOPE;
try {
  AZURE_AD_SCOPE = JSON.parse(AZURE_AD_SCOPE);
} catch (error) {
  console.error("Parsing error - AZURE_AD_SCOPE: ", error);
}
export const BACKEND_URL = process.env.VITE_BACKEND_URL?.endsWith("/")
  ? process.env.VITE_BACKEND_URL
  : process.env.VITE_BACKEND_URL + "/";

export const APP_TITLE = process.env.VITE_TITLE;
export const APP_VERSION = process.env.VITE_APP_VERSION;
export const APP_LOGO = process.env.VITE_LOGO || "";

export const APP_RIGHT_LOGO = process.env.VITE_RIGHT_LOGO || "";

export const APP_LOGO_DISPLAY_ON_LOGIN_PAGE =
  process.env.VITE_LOGO_DISPLAY_ON_LOGIN_PAGE || true;

export const SQL_DISPLAY = process.env.VITE_SQL_DISPLAY;

// https://cloudscape.design/patterns/general/density-settings/
export const APP_STYLE_DEFAULT_COMPACT = true;

export const OIDC = {
  ISSUER: process.env.VITE_OIDC_ISSUER,
  CLIENT_ID: process.env.VITE_OIDC_CLIENT_ID,
  URL_LOGOUT: process.env.VITE_OIDC_URL_LOGOUT,
  URL_REDIRECT: process.env.VITE_OIDC_URL_REDIRECT,
} as const;

export const LOCAL_STORAGE_KEYS = {
  accessToken: "accessToken",
  idToken: "idToken",
  refreshToken: "refreshToken",
  oidcUser: `oidc.user:${OIDC.ISSUER}:${OIDC.CLIENT_ID}`,
  azureAd: `msal.token.keys.${OIDC.CLIENT_ID}`,
} as const;
