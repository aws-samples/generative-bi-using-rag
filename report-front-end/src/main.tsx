import "@cloudscape-design/global-styles/index.css";
import React from "react";
import ReactDOM from "react-dom/client";
import { Provider } from "react-redux";
import "regenerator-runtime/runtime";
import { isLoginWithCognito, LOGIN_TYPE } from "./common/constant/constants";
import { Storage } from "./common/helpers/storage";
import userReduxStore from "./common/helpers/store";
import AppConfigured from "./pages/login-page/cognito-login-page";
import CustomLogin from "./pages/login-page/custom-login-page";

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
      {isLoginWithCognito ? <AppConfigured /> : <CustomLogin />}
    </Provider>
  </React.StrictMode>
);
