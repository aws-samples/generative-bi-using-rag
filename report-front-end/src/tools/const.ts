export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL?.endsWith("/")
  ? process.env.REACT_APP_BACKEND_URL
  : process.env.REACT_APP_BACKEND_URL + "/";

export const APP_TITLE = process.env.REACT_APP_TITLE;

export const APP_LOGO = process.env.REACT_APP_LOGO || '';

export const SQL_DISPLAY = process.env.REACT_APP_SQL_DISPLAY;

export const AMPLIFY_CONFIG_JSON = "__bi_demo_app_amplify_config_json__";

export const LOCALSTORAGE_KEY = "__GEN_BI_STORE_INFO__";
