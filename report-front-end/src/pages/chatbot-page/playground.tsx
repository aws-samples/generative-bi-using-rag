import { Auth } from "aws-amplify";
import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { v4 as uuid } from "uuid";
import BaseAppLayout from "../../components/app-layout";
import Chat from "../../components/chatbot-panel/chat";
import ConfigPanel from "../../components/config-panel";
import { Session } from "../../components/session-panel/types";
import NavigationPanel from "../../components/side-navigation";

export default function Playground() {
  const [toolsHide, setToolsHide] = useState(true);

  const dispatch = useDispatch();
  // const userState = useSelector<UserState>((state) => state) as UserState;

  useEffect(() => {
    const handleUnAuthorized = () => {
      console.info("handleUnAuthorized fired!");
      Auth.signOut().then();
    };

    const handleAuthorized = (event: Event) => {
      const e = event as CustomEvent;
      if (e.detail) {
        // const userInfo: UserInfo = {
        //   ...userState.userInfo,
        //   userId: e.detail.userId,
        //   displayName: e.detail.userName,
        // };
        // dispatch({ type: ActionType.UpdateUserInfo, state: userInfo });
      }
    };
    window.addEventListener("unauthorized", () => handleUnAuthorized());
    window.addEventListener("authorized", (event) => handleAuthorized(event));
    return () => {
      window.removeEventListener("unauthorized", () => handleUnAuthorized());
      window.removeEventListener("authorized", (event) =>
        handleAuthorized(event)
      );
    };
  }, [dispatch]);

  const [sessions, setSessions] = useState<Session[]>([{
    session_id: uuid(),
    title: "New Chat",
    messages: [],
  }]);
  const [currentSessionId, setCurrentSessionId] = useState<string>(sessions[0].session_id);

  return (
    <BaseAppLayout
      info={<ConfigPanel setToolsHide={setToolsHide} />}
      navigation={
        <NavigationPanel
          sessions={sessions}
          setSessions={setSessions}
          currentSessionId={currentSessionId}
          setCurrentSessionId={setCurrentSessionId}
        />
      }
      content={
        <Chat
          toolsHide={toolsHide}
          setToolsHide={setToolsHide}
          sessions={sessions}
          setSessions={setSessions}
          currentSessionId={currentSessionId}
          setCurrentSessionId={setCurrentSessionId}
        />
      }
      toolsHide={toolsHide}
      setToolsHide={setToolsHide}
    />
  );
}
