import { createStore } from "redux";
import { ActionType, UserAction, UserState } from "./types";
import { DEFAULT_QUERY_CONFIG, LOCALSTORAGE_KEY } from "../../common/constant/constants";

const defaultUserState: UserState = {
  userId: "",
  account: "",
  displayName: "",
  email: "@amazon.com",
  loginExpiration: +new Date() + 6000,
  queryConfig: DEFAULT_QUERY_CONFIG,
};

const localStorageData = localStorage.getItem(LOCALSTORAGE_KEY)
  ? JSON.parse(localStorage.getItem(LOCALSTORAGE_KEY) || "{}")
  : null;

const initialState = localStorageData || defaultUserState;

const userReducer = (state = initialState, action: UserAction) => {
  switch (action.type) {
    case ActionType.Update:
      localStorage.setItem(
        LOCALSTORAGE_KEY,
        JSON.stringify({ ...action.state })
      );
      return { ...action.state };
    case ActionType.Delete:
      localStorage.setItem(LOCALSTORAGE_KEY, "");
      return null;
    case ActionType.UpdateConfig:
      if (localStorage.getItem(LOCALSTORAGE_KEY)) {
        const userInfo = JSON.parse(localStorage.getItem(LOCALSTORAGE_KEY) || "");
        userInfo.queryConfig = action.state.queryConfig;
        localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify({ ...userInfo }));
      }
      return { ...action.state };
    default:
      return { ...state };
  }
};

const store = createStore(userReducer as any);

export default store;
