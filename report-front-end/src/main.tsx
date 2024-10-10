import "@cloudscape-design/global-styles/index.css";
import React from "react";
import ReactDOM from "react-dom/client";
import { Provider } from "react-redux";
import "regenerator-runtime/runtime";
import Login from "./components/Login";
import {
  AUTH_WITH_OIDC,
  AUTH_WITH_COGNITO,
  LOGIN_TYPE,
  AUTH_WITH_SSO,
  AUTH_WITH_AZUREAD,
} from "./utils/constants";
import { Storage } from "./utils/helpers/storage";
import userReduxStore from "./utils/helpers/store";

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);

const theme = Storage.getTheme();
Storage.applyTheme(theme);
const density = Storage.getDensity();
Storage.applyDensity(density);
console.log("Authentication/Login type: ", LOGIN_TYPE);

let rootComponent = <Login.Custom />;

if (AUTH_WITH_COGNITO) {
  rootComponent = <Login.Cognito />;
}
if (AUTH_WITH_OIDC) {
  rootComponent = <Login.Oidc />;
}
if (AUTH_WITH_SSO) {
  rootComponent = <Login.Sso />;
}
if (AUTH_WITH_AZUREAD) {
  rootComponent = <Login.AzureAd />;
}

root.render(
  <React.StrictMode>
    <Provider store={userReduxStore}>{rootComponent}</Provider>
  </React.StrictMode>
);
