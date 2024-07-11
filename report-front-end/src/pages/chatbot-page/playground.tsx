import { useState } from "react";
import ConfigPanel from "../../components/config-panel";
import BaseAppLayout from "../../components/app-layout";
import Chat from "../../components/chatbot-panel/chat";

export default function Playground() {
  const [toolsHide, setToolsHide] = useState(true);

  return (
    <BaseAppLayout
      info={<ConfigPanel setToolsHide={setToolsHide} />}
      content={<Chat toolsHide={toolsHide} setToolsHide={setToolsHide}/>}
      toolsHide={toolsHide}
      setToolsHide={setToolsHide}
    />
  );
}
