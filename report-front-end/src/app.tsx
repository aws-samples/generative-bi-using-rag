import "./app.scss";
import PageRouter from "./pages/page-router";
import CustomTopNavigation from "./components/top-navigation";
import { BrowserRouter } from "react-router-dom";
import { useEffect, useState } from "react";
import { Auth } from "aws-amplify";
import { useDispatch } from "react-redux";
import { ActionType, UserInfo } from "./common/helpers/types";
import AlertMsg from "./components/alert-msg";

function App() {

  const [user, setUser] = useState<any>(null);

  const dispatch = useDispatch();

  useEffect(() => {
    (async () => {
      const user = await Auth.currentUserInfo();
      setUser(user);
    })();
  }, []);

    useEffect(() => {
    const loginUser: UserInfo = {
      userId: user?.attributes?.sub || "",
      displayName: user?.attributes?.displayName || user?.attributes?.email || "",
      loginExpiration: + new Date() + 18000000,
      isLogin: true
    };
    dispatch({ type: ActionType.UpdateUserInfo, state: loginUser });
  }, [user]);

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
