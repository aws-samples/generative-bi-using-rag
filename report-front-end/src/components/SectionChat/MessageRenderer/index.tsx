import { Icon, SpaceBetween } from "@cloudscape-design/components";
import { Dispatch, SetStateAction } from "react";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import { ChatBotHistoryItem, ChatBotMessageType } from "../types";
import styles from "../chat.module.scss";
import AiMessage from "./AiMessage";

export interface ChatMessageProps<T = ChatBotHistoryItem> {
  message: T;
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
  sendJsonMessage: SendJsonMessage;
}

export default function MessageRenderer({
  message,
  sendJsonMessage,
}: ChatMessageProps) {
  return (
    <SpaceBetween size="xs">
      {message.type === ChatBotMessageType.Human && (
        <div className={styles.question}>
          <Icon name="user-profile" /> {message?.content?.toString()}
        </div>
      )}
      {message.type === ChatBotMessageType.AI && (
        <AiMessage {...{ message, sendJsonMessage }} />
      )}
    </SpaceBetween>
  );
}
