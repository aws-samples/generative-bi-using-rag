import "./app.scss";
import PageRouter from "./pages/page-router";
import CustomTopNavigation from "./components/top-navigation";
import { BrowserRouter } from "react-router-dom";
import { useEffect } from "react";
import { Auth } from "aws-amplify";
import { useDispatch } from "react-redux";
import { ActionType, UserInfo } from "./common/helpers/types";
import AlertMsg from "./components/alert-msg";
import { COGNITO, LOGIN_TYPE } from "./common/constant/constants";

function App() {

  const dispatch = useDispatch();

  useEffect(() => {
    if (LOGIN_TYPE === COGNITO) {
      (async () => {
        const user = await Auth.currentUserInfo();
        const loginUser: UserInfo = {
          userId: user?.attributes?.sub || "",
          displayName: user?.attributes?.displayName || user?.attributes?.email || "",
          loginExpiration: 0,
          isLogin: true
        };
        dispatch({type: ActionType.UpdateUserInfo, state: loginUser});
      })();
    } else {
      const loginUser: UserInfo = {
        userId: "",
        displayName: "",
        loginExpiration: 0,
        isLogin: true
      };
      dispatch({type: ActionType.UpdateUserInfo, state: loginUser});
    }
  }, []);

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
