import { AmplifyUser } from "@aws-amplify/ui";
import { useEffect } from "react";
import { useDispatch } from "react-redux";
import { BrowserRouter } from "react-router-dom";
import "./app.scss";
import { COGNITO, LOGIN_TYPE } from "./common/constant/constants";
import { ActionType, UserInfo } from "./common/helpers/types";
import AlertMsg from "./components/alert-msg";
import CustomTopNavigation from "./components/top-navigation";
import { UseAuthenticator } from "@aws-amplify/ui-react-core";
import PageRouter from "./pages/page-router";

export type SignOut = UseAuthenticator["signOut"];

function App({ user }: { signOut?: SignOut; user?: AmplifyUser }) {
  console.log({ user });

  const dispatch = useDispatch();

  useEffect(() => {
    if (LOGIN_TYPE === COGNITO) {
      const loginUser: UserInfo = {
        userId: user?.attributes?.sub || "",
        displayName:
          user?.attributes?.displayName || user?.attributes?.email || "",
        loginExpiration: 0,
        isLogin: true,
      };
      dispatch({ type: ActionType.UpdateUserInfo, state: loginUser });
    } else {
      const loginUser: UserInfo = {
        userId: "none",
        displayName: "",
        loginExpiration: 0,
        isLogin: true,
      };
      dispatch({ type: ActionType.UpdateUserInfo, state: loginUser });
    }
  }, [dispatch, user]);

  return (
    <div style={{ height: "100%" }}>
      <BrowserRouter>
        <AlertMsg />
        <CustomTopNavigation />
        <div style={{ height: "56px", backgroundColor: "#000716" }}>&nbsp;</div>
        <div>
          <PageRouter />
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;
