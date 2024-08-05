import { useEffect, useState } from "react";
import ConfigPanel from "../../components/config-panel";
import BaseAppLayout from "../../components/app-layout";
import Chat from "../../components/chatbot-panel/chat";
import ErrorPage from "../error-page";
import { useLocation } from "react-router-dom";
import { Global } from "../../common/constant/global";
import { ActionType, UserInfo, UserState } from "../../common/helpers/types";
import { useDispatch, useSelector } from "react-redux";
import NavigationPanel from "../../components/side-navigation";
import { Session } from "../../components/session-panel/types";
import { v4 as uuid } from "uuid";

export default function Playground() {
  const [toolsHide, setToolsHide] = useState(true);
  const [authentication, setAuthentication] = useState(true);

  const { search } = useLocation();
  const params = new URLSearchParams(search);
  Global.profile = params.get("profile") || "";

  const dispatch = useDispatch();
  const userState = useSelector<UserState>((state) => state) as UserState;

  const showErrorPage = (isAuthentication: boolean) => {
    setAuthentication(isAuthentication);
  };

  const updateUserInfo = (event: Event) => {
    const e = event as CustomEvent;
    if (e.detail) {
      const userInfo: UserInfo = {
        ...userState.userInfo,
        userId: e.detail.userId,
        displayName: e.detail.userName,
      };
      dispatch({ type: ActionType.UpdateUserInfo, state: userInfo });
    }
  };

  useEffect(() => {
    window.addEventListener("unauthorized", () => showErrorPage(false));
    window.addEventListener("authorized", (event) => updateUserInfo(event));
    return () => {
      window.removeEventListener("unauthorized", () => showErrorPage(false));
      window.removeEventListener("authorized", (event) => updateUserInfo(event));
    };
  }, []);

  const [sessions, setSessions] = useState<Session[]>([{
    session_id: uuid(),
    messages: [],
  }]);
  const [currentSession, setCurrentSession] = useState<number>(0);

  return (
    authentication ?
      <BaseAppLayout
        info={<ConfigPanel setToolsHide={setToolsHide} />}
        navigation={
          <NavigationPanel
            sessions={sessions}
            setSessions={setSessions}
            currentSession={currentSession}
            setCurrentSession={setCurrentSession}
          />
        }
        content={
          <Chat
            toolsHide={toolsHide}
            setToolsHide={setToolsHide}
            sessions={sessions}
            setSessions={setSessions}
            currentSession={currentSession}
          />
        }
        toolsHide={toolsHide}
        setToolsHide={setToolsHide}
      /> : <ErrorPage />
  );
}
