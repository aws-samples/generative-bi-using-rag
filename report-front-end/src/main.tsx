import "@cloudscape-design/global-styles/index.css";
import React from "react";
import ReactDOM from "react-dom/client";
import { Provider } from "react-redux";
import "regenerator-runtime/runtime";
import Login from "./components/Login";
import { isLoginWithCognito, LOGIN_TYPE } from "./utils/constants";
import { Storage } from "./utils/helpers/storage";
import userReduxStore from "./utils/helpers/store";

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);

const theme = Storage.getTheme();
Storage.applyTheme(theme);
const density = Storage.getDensity();
Storage.applyDensity(density);
console.log("Login type: ", LOGIN_TYPE);

root.render(
  <React.StrictMode>
    <Provider store={userReduxStore}>
      {isLoginWithCognito ? <Login.Cognito /> : <Login.Custom />}
    </Provider>
  </React.StrictMode>
);
