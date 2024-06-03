import React, { useEffect } from "react";
import "./App.css";
import "@cloudscape-design/global-styles/index.css";
import PageRouter from "./components/page-router";
import AlertMsg from "./components/alert-msg";
import { ActionType, UserState } from "./types/StoreTypes";
import { useDispatch, useSelector } from "react-redux";
import LoginPage from "./components/login-page";

function App() {
  const userInfo = useSelector<UserState>((state) => state) as UserState;
  const dispatch = useDispatch();
  useEffect(() => {
    checkLoginStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const checkLoginStatus = () => {
    if (userInfo.loginExpiration < +new Date()) {
      dispatch({ type: ActionType.Delete });
    }
  };
  return (
    <div style={{ height: "100%" }}>
      <AlertMsg />
      {(!userInfo || !userInfo.userId || userInfo.userId === "") && (
        <LoginPage />
      )}
      {userInfo && userInfo.userId && userInfo.userId !== "" && (
        <PageRouter />
      )}
    </div>
  );
}

export default App;
