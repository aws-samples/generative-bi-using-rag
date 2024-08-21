import { Button } from "@aws-amplify/ui-react";
import { Dispatch, SetStateAction } from "react";
import { ChatBotHistoryItem } from "./types";
import styles from "./chat.module.scss";
import { useSelector } from "react-redux";
import {  useQueryWithCookies } from "../../common/api/WebSocket";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import { UserState } from "../../common/helpers/types";
import { Session } from "../session-panel/types";

export interface SuggestedQuestionsProps {
  questions: string[];
  setLoading: Dispatch<SetStateAction<boolean>>;
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
  setSessions: Dispatch<SetStateAction<Session[]>>;
  sendMessage: SendJsonMessage;
  sessionId: string;
}

export default function SuggestedQuestions(props: SuggestedQuestionsProps) {
  const { queryWithWS } = useQueryWithCookies();

  const userState = useSelector<UserState>((state) => state) as UserState;

  const handleSendMessage = (question: string) => {
    // Call WebSocket API
    queryWithWS({
      query: question,
      configuration: userState.queryConfig,
      sendMessage: props.sendMessage,
      setMessageHistory: props.setMessageHistory,
      setSessions: props.setSessions,
      userId: userState.userInfo.userId,
      sessionId: props.sessionId,
      username: userState.userInfo.username,
    });
  };

  return (
    <div className={styles.questions_grid}>
      {props.questions.map((question, kid) => (
        <Button
          key={kid}
          size="small"
          className={styles.button}
          onClick={() => handleSendMessage(question)}>
          {question}
        </Button>
      ))}
    </div>
  );
}
