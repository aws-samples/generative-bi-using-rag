import { Button, Input } from "@cloudscape-design/components";
import React, { useState } from "react";
import { alertMsg, showHideSpinner } from "../../tools/tool";
import { useDispatch } from "react-redux";
import "./style.scss";
import { ActionType, UserState } from "../../types/StoreTypes";
import { DEFAULT_QUERY_CONFIG } from "../../enum/DefaultQueryEnum";

const LoginPage = () => {
  const [userName, setUserName] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoding] = useState(false);
  const dispatch = useDispatch();

  const closeWindow = () => {
    window.location.href = "about:blank";
    window.close();
  };

  const doLogin = async () => {
    setIsLoding(true);
    const reg =
      /^\w+((.\w+)|(-\w+))@[A-Za-z0-9]+((.|-)[A-Za-z0-9]+).[A-Za-z0-9]+$/;
    if (!userName || !reg.test(userName)) {
      alertMsg("Please enter your vaild email", "warning");
      setIsLoding(false);
      return;
    }
    if (!password) {
      alertMsg("Please enter your password", "warning");
      setIsLoding(false);
      return;
    }
    if (userName !== "bi_example@amazon.com" || password !== "HiGenBI@2024") {
      alertMsg("Username or password is error", "warning");
      setIsLoding(false);
      return;
    }

    showHideSpinner(true);
    try {
      showHideSpinner(false);

      alertMsg("Login success", "success");
      const loginUser: UserState = {
        userId: "bi_example",
        email: "bi_example@amazon.com",
        account: "bi_example",
        displayName: "bi_example",
        loginExpiration: +new Date() + 18000000,
        queryConfig: DEFAULT_QUERY_CONFIG,
      };
      dispatch({ type: ActionType.Update, state: loginUser });
      setIsLoding(false);
    } catch (error) {
      showHideSpinner(false);
      alertMsg("Wrong user name or password", "error");
      setIsLoding(false);
    }
  };

  return (
    <div className="login-page">
      <span className="login-page-title">Data Mesh Login</span>
      <div className="login-page-name">
        <span className="login-page-span">User Name:</span>
        <Input
          className="login-page-input"
          value={userName}
          onChange={({ detail }) => setUserName(detail.value)}
          placeholder="**@your_domain.com"
        />
      </div>
      <div className="login-page-pwd">
        <span className="login-page-span">Password:</span>
        <Input
          className="login-page-input"
          type="password"
          value={password}
          onChange={({ detail }) => setPassword(detail.value)}
          placeholder="your password"
        />
      </div>
      <div className="login-page-btn">
        <Button
          variant="primary"
          className="login"
          onClick={doLogin}
          disabled={isLoading}
        >
          Login
        </Button>
        <Button onClick={closeWindow}>Close Page</Button>
      </div>
      <div
        className="login-page-support"
        onClick={() => {
          window.open("/register-guidence.html", "_blank");
        }}
      >
        How to register a new domain?
      </div>
    </div>
  );
};

export default LoginPage;
