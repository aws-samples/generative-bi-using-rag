import { useState } from "react";
import { ChatBotConfiguration, } from "./types";
import ChatInputPanel from "./chat-input-panel";
import styles from "../../styles/chat.module.scss";

export default function Chat() {
  const [running, setRunning] = useState<boolean>(false);
  const [configuration, setConfiguration] = useState<ChatBotConfiguration>(
    () => ({
      streaming: true,
      showMetadata: false,
      maxTokens: 512,
      temperature: 0.6,
      topP: 0.9,
      files: null,
    })
  );

  return (
    <div className={styles.chat_container}>
      <div className={styles.welcome_text}>
        <center>{'GenBI Chatbot'}</center>
      </div>
      <div className={styles.input_container}>
        <ChatInputPanel
          running={running}
          setRunning={setRunning}
          configuration={configuration}
          setConfiguration={setConfiguration}
        />
      </div>
    </div>
  );
}
