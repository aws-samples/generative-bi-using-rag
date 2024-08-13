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
        />
      }
      toolsHide={toolsHide}
      setToolsHide={setToolsHide}
    />
  );
}
