import { AmplifyUser } from "@aws-amplify/ui";
import { UseAuthenticator } from "@aws-amplify/ui-react-core";
import { useEffect, useState } from "react";
import toast, { Toaster } from "react-hot-toast";
import { useDispatch } from "react-redux";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { v4 as uuid } from "uuid";
import "./app.scss";
import BaseAppLayout from "./components/BaseAppLayout";
import PanelConfigs from "./components/PanelConfigs";
import { PanelSideNav } from "./components/PanelSideNav";
import { Session } from "./components/PanelSideNav/types";
import SectionChat from "./components/SectionChat";
import TopNav from "./components/TopNav";
import { GlobalContext } from "./hooks/useGlobalContext";
import { isLoginWithCognito, LOCAL_STORAGE_KEYS } from "./utils/constants";
import { ActionType, UserInfo } from "./utils/helpers/types";

export type SignOut = UseAuthenticator["signOut"];

const App: React.FC<{
  signOut?: SignOut;
  user?: AmplifyUser & { signInUserSession: any };
}> = ({ user }) => {
  const dispatch = useDispatch();
  console.log({ user, signInUserSession: user?.signInUserSession });

  useEffect(() => {
    if (isLoginWithCognito) {
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
          username: user?.username || "",
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
        username: "anonymous",
      };
      dispatch({ type: ActionType.UpdateUserInfo, state: loginUser });
    }
  }, [dispatch, user]);

  return (
    <div style={{ height: "100%" }}>
      <BrowserRouter>
        <Toaster />
        <TopNav />
        <div style={{ height: "56px", backgroundColor: "#000716" }}>&nbsp;</div>
        <div>
          <Routes>
            <Route index path="/" element={<Playground />} />
          </Routes>
        </div>
      </BrowserRouter>
    </div>
  );
};

export default App;

const initSession = () => ({
  session_id: uuid(),
  title: "New Chat",
  messages: [],
});

function Playground() {
  const [toolsHide, setToolsHide] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([initSession()]);
  const [currentSessionId, setCurrentSessionId] = useState(
    sessions[0].session_id
  );
  return (
    <GlobalContext.Provider
      value={{
        sessions,
        setSessions,
        currentSessionId,
        setCurrentSessionId,
        isSearching,
        setIsSearching,
      }}
    >
      <BaseAppLayout
        navigation={<PanelSideNav />}
        content={<SectionChat {...{ toolsHide, setToolsHide }} />}
        tools={<PanelConfigs setToolsHide={setToolsHide} />}
        toolsHide={toolsHide}
        setToolsHide={setToolsHide}
      />
    </GlobalContext.Provider>
  );
}
