import { Button } from "@aws-amplify/ui-react";
import { Link, SpaceBetween } from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import { getRecommendQuestions } from "../../common/api/API";
import { useQueryWithCookies } from "../../common/api/WebSocket";
import { UserState } from "../../common/helpers/types";
import styles from "./chat.module.scss";
import { ChatBotHistoryItem, ChatInputState } from "./types";
import { Session } from "../session-panel/types";

export interface RecommendQuestionsProps {
  setTextValue: Dispatch<SetStateAction<ChatInputState>>;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
  setSessions: Dispatch<SetStateAction<Session[]>>;
  sendMessage: SendJsonMessage;
  sessionId: string;
}

export default function CustomQuestions(props: RecommendQuestionsProps) {
  const [showMoreQuestions, setShowMoreQuestions] = useState(true);
  const [questions, setQuestions] = useState<string[]>([]);
  const { queryWithWS } = useQueryWithCookies();
  const userState = useSelector<UserState>((state) => state) as UserState;

  useEffect(() => {
    const data_profile = userState.queryConfig?.selectedDataPro;
    if (data_profile) {
      getRecommendQuestions(data_profile).then((data) => {
        setQuestions(data);
      });
    }
  }, [userState.queryConfig?.selectedDataPro]);

  const handleSendMessage = (question: string) => {
    // Call Fast API
    /*query({
      query: question,
      setLoading: props.setLoading,
      configuration: userState.queryConfig,
      setMessageHistory: props.setMessageHistory
    }).then();*/
    setShowMoreQuestions(true);
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
    <div>
      {questions?.length > 0 && showMoreQuestions && (
        <SpaceBetween size={"xxs"}>
          <div className={styles.questions_grid}>
            {questions
              ?.slice(0, Math.min(3, questions.length))
              .map((question, kid) => (
                <Button
                  key={kid}
                  size="small"
                  className={styles.button}
                  onClick={() => handleSendMessage(question)}
                >
                  {question}
                </Button>
              ))}
          </div>
          <div style={{ float: "right" }}>
            <Link
              variant="primary"
              onFollow={() => setShowMoreQuestions(false)}
            >
              <p className={styles.text}>More sample suggestions</p>
            </Link>
          </div>
        </SpaceBetween>
      )}
      {questions?.length > 0 && !showMoreQuestions && (
        <SpaceBetween size={"xxs"}>
          <div className={styles.questions_grid}>
            {questions?.map((question, kid) => (
              <Button
                key={kid}
                size="small"
                className={styles.button}
                onClick={() => handleSendMessage(question)}
              >
                {question}
              </Button>
            ))}
          </div>
          <div style={{ float: "right" }}>
            <Link variant="primary" onFollow={() => setShowMoreQuestions(true)}>
              <p className={styles.text}>Less sample suggestions</p>
            </Link>
          </div>
        </SpaceBetween>
      )}
    </div>
  );
}
