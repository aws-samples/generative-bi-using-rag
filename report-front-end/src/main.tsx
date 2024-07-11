import "regenerator-runtime/runtime";
import React from "react";
import ReactDOM from "react-dom/client";
import { Storage } from "./common/helpers/storage";
import "@cloudscape-design/global-styles/index.css";
import { Provider } from "react-redux";
import userReduxStore from "./common/helpers/store";
import AppConfigured from "./pages/login-page";
import { applyDensity, Density } from "@cloudscape-design/global-styles";
import { COMPACT_STYLE } from "./common/constant/constants";

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);

const theme = Storage.getTheme();
Storage.applyTheme(theme);
applyDensity(COMPACT_STYLE ? Density.Compact : Density.Comfortable);

root.render(
  <React.StrictMode>
    <Provider store={userReduxStore}>
      <AppConfigured />
    </Provider>
  </React.StrictMode>
);
