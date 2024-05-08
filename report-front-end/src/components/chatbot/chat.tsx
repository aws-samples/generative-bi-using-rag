import { SetStateAction, useState } from "react";
import { ChatBotConfiguration, ChatBotHistoryItem } from "./types";
import ChatInputPanel from "./chat-input-panel";
import styles from "../../styles/chat.module.scss";
import { Box, SpaceBetween, Spinner } from "@cloudscape-design/components";
import ChatMessage from "./chat-message";

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

  const [messageHistory, setMessageHistory] = useState<ChatBotHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  return (
    <div className={styles.chat_container}>
      <SpaceBetween size={'l'}>
        {messageHistory.map((message, idx) => (
          <ChatMessage
            key={idx}
            message={message}
            onThumbsUp={() => {
            }}
            onThumbsDown={() => {
            }}/>
        ))}
        {loading && (
          <Box float="left">
            <Spinner/>
          </Box>
        )}
      </SpaceBetween>
      <div className={styles.welcome_text}>
        {messageHistory.length === 0 && !loading && (
          <center>{'GenBI Chatbot'}</center>
        )}
      </div>
      <div className={styles.input_container}>
        <ChatInputPanel
          running={running}
          setLoading={setLoading}
          configuration={configuration}
          setConfiguration={setConfiguration}
          messageHistory={messageHistory}
          setMessageHistory={(history: SetStateAction<ChatBotHistoryItem[]>) => setMessageHistory(history)}
        />
      </div>
    </div>
  );
}
