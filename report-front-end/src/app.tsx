import { AmplifyUser } from "@aws-amplify/ui";
import { UseAuthenticator } from "@aws-amplify/ui-react-core";
import { useEffect } from "react";
import toast, { Toaster } from "react-hot-toast";
import { useDispatch } from "react-redux";
import { BrowserRouter } from "react-router-dom";
import "./app.scss";
import {
  COGNITO,
  LOCAL_STORAGE_KEYS,
  LOGIN_TYPE,
} from "./common/constant/constants";
import { ActionType, UserInfo } from "./common/helpers/types";
import AlertMsg from "./components/alert-msg";
import CustomTopNavigation from "./components/top-navigation";
import PageRouter from "./pages/page-router";

export type SignOut = UseAuthenticator["signOut"];

const App: React.FC<{
  signOut?: SignOut;
  user?: AmplifyUser & { signInUserSession: any };
}> = ({ user }) => {
  const dispatch = useDispatch();
  console.log({ user, signInUserSession: user?.signInUserSession });

  useEffect(() => {
    if (LOGIN_TYPE === COGNITO) {
      if (!user?.signInUserSession) {
        toast.error("User session not found");
        return;
      }
      try {
        const {
          signInUserSession: {
            accessToken: { jwtToken: accessToken },
            idToken: { jwtToken: idToken },
            refreshToken: { token: refreshToken },
          },
        } = user;
        const loginUser: UserInfo = {
          userId: user?.attributes?.sub || "",
          displayName:
            user?.attributes?.displayName || user?.attributes?.email || "",
          loginExpiration: 0,
          isLogin: true,
        };
        dispatch({ type: ActionType.UpdateUserInfo, state: loginUser });
        localStorage.setItem(LOCAL_STORAGE_KEYS.accessToken, accessToken);
        localStorage.setItem(LOCAL_STORAGE_KEYS.idToken, idToken);
        localStorage.setItem(LOCAL_STORAGE_KEYS.refreshToken, refreshToken);
      } catch (error) {
        console.error("Initiating cognito user state error: ", error);
      }
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
        <Toaster />
        <AlertMsg />
        <CustomTopNavigation />
        <div style={{ height: "56px", backgroundColor: "#000716" }}>&nbsp;</div>
        <div>
          <PageRouter />
        </div>
      </BrowserRouter>
    </div>
  );
};

export default App;
