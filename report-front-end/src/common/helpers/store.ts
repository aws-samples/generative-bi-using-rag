import { createStore } from "redux";
import { DEFAULT_QUERY_CONFIG, DEFAULT_USER_INFO, LOCALSTORAGE_KEY } from "../constant/constants";
import { ActionType, UserAction, UserState } from "./types";

const defaultUserState: UserState = {
  userInfo : DEFAULT_USER_INFO,
  queryConfig: DEFAULT_QUERY_CONFIG,
};

const localStorageData = localStorage.getItem(LOCALSTORAGE_KEY)
  ? JSON.parse(localStorage.getItem(LOCALSTORAGE_KEY) || "{}")
  : null;

const initialState = localStorageData || defaultUserState;

const userReducer = (state = initialState, action: UserAction) => {
  switch (action.type) {
    case ActionType.Delete:
      localStorage.setItem(LOCALSTORAGE_KEY, "");
      return null;
    case ActionType.UpdateUserInfo:
      localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify({ ...state, userInfo: action.state }));
      return { ...state, userInfo: action.state };
    case ActionType.UpdateConfig:
      localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify({ ...state, queryConfig: action.state }));
      return { ...state, queryConfig: action.state };
    default:
      localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify({ ...state }));
      return { ...state };
  }
};

const store = createStore(userReducer as any);

export default store;
