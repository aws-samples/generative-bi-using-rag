import { useState } from "react";
import { v4 as uuid } from "uuid";
import BaseAppLayout from "../../components/app-layout";
import Chat from "../../components/chatbot-panel/chat";
import ConfigPanel from "../../components/config-panel";
import { Session } from "../../components/session-panel/types";
import NavigationPanel from "../../components/side-navigation";

export default function Playground() {
  const [toolsHide, setToolsHide] = useState(true);

  const [sessions, setSessions] = useState<Session[]>([
    {
      session_id: uuid(),
      title: "New Chat",
      messages: [],
    },
  ]);
  const [currentSessionId, setCurrentSessionId] = useState<string>(
    sessions[0].session_id
  );

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
