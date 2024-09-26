import { Icon, SpaceBetween } from "@cloudscape-design/components";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import styles from "../chat.module.scss";
import { ChatBotHistoryItem, ChatBotMessageType } from "../types";
import AiMessage from "./AiMessage";

export interface MessageRendererProps<T = ChatBotHistoryItem> {
  message: T;
  sendJsonMessage: SendJsonMessage;
}

export default function MessageRenderer({
  message,
  sendJsonMessage,
}: MessageRendererProps) {
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
