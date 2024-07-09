import "regenerator-runtime/runtime";
import React from "react";
import ReactDOM from "react-dom/client";
import { Storage } from "./common/helpers/storage";
import "@cloudscape-design/global-styles/index.css";
import { Provider } from "react-redux";
import userReduxStore from "./common/helpers/store";
import AppConfigured from "./pages/login-page";
import { applyDensity, Density } from "@cloudscape-design/global-styles";

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);

const theme = Storage.getTheme();
Storage.applyTheme(theme);
// TODO: decide whether to add an env var for this style switch?
const useCompactStyle = true;
applyDensity(useCompactStyle ? Density.Compact : Density.Comfortable);

root.render(
  <React.StrictMode>
    <Provider store={userReduxStore}>
      <AppConfigured />
    </Provider>
  </React.StrictMode>
);
