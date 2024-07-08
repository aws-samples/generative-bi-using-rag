import "./app.scss";
import PageRouter from "./pages/page-router";
import CustomTopNavigation from "./components/top-navigation";
import { BrowserRouter } from "react-router-dom";
import { useEffect, useState } from "react";
import { Auth } from "aws-amplify";
import { useDispatch } from "react-redux";
import { DEFAULT_QUERY_CONFIG } from "./common/constant/constants";
import { ActionType, UserState } from "./common/helpers/types";
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
    const loginUser: UserState = {
      userId: user?.attributes?.sub || "",
      email: user?.attributes?.email || "",
      displayName: user?.attributes?.displayName || "",
      loginExpiration: + new Date() + 18000000,
      queryConfig: DEFAULT_QUERY_CONFIG,
    };
    dispatch({ type: ActionType.Update, state: loginUser });
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
