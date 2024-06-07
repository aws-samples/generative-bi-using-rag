import { Button } from "@aws-amplify/ui-react";
import { Dispatch, SetStateAction } from "react";
import { ChatBotHistoryItem } from "./types";
import styles from "./chat.module.scss";
import { query } from "../../common/api/API";
import { useSelector } from "react-redux";
import { UserState } from "../config-panel/types";

export interface SuggestedQuestionsProps {
  questions: string[];
  setLoading: Dispatch<SetStateAction<boolean>>;
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
}

export default function SuggestedQuestions(props: SuggestedQuestionsProps) {

  const userInfo = useSelector<UserState>((state) => state) as UserState;

  const handleSendMessage = (question: string) => {
    query({
      query: question,
      setLoading: props.setLoading,
      configuration: userInfo.queryConfig,
      setMessageHistory: props.setMessageHistory
    }).then();
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