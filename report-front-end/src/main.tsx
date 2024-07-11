import "@cloudscape-design/global-styles/index.css";
import React from "react";
import ReactDOM from "react-dom/client";
import { Provider } from "react-redux";
import "regenerator-runtime/runtime";
import { Storage } from "./common/helpers/storage";
import userReduxStore from "./common/helpers/store";
import AppConfigured from "./pages/login-page";

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);

const theme = Storage.getTheme();
Storage.applyTheme(theme);
const density = Storage.getDensity();
Storage.applyDensity(density);

root.render(
  <React.StrictMode>
    <Provider store={userReduxStore}>
      <AppConfigured />
    </Provider>
  </React.StrictMode>
);
