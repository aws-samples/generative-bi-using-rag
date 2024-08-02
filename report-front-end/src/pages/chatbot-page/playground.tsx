import { useState } from "react";
import ConfigPanel from "../../components/config-panel";
import BaseAppLayout from "../../components/app-layout";
import Chat from "../../components/chatbot-panel/chat";
import NavigationPanel from "../../components/side-navigation";
import { Session } from "../../components/session-panel/types";
import { v4 as uuid } from "uuid";

export default function Playground() {
  const [toolsHide, setToolsHide] = useState(true);

  const [sessions, setSessions] = useState<Session[]>([{
    session_id: uuid(),
    messages: [],
  }]);
  const [currentSession, setCurrentSession] = useState<number>(0);

  return (
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
    />
  );
}
