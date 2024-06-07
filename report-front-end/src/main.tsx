import "regenerator-runtime/runtime";
import React from "react";
import ReactDOM from "react-dom/client";
import { Storage } from "./common/helpers/storage";
import "@cloudscape-design/global-styles/index.css";
import { Provider } from "react-redux";
import userReduxStore from "./components/config-panel/store";
import AppConfigured from "./components/login-page";

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);

const theme = Storage.getTheme();
Storage.applyTheme(theme);

root.render(
  <React.StrictMode>
    <Provider store={userReduxStore}>
      <AppConfigured />
    </Provider>
  </React.StrictMode>
);
