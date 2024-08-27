import { Button } from "@aws-amplify/ui-react";
import { Link, SpaceBetween } from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import { getRecommendQuestions } from "../../utils/api/API";
import { useQueryWithTokens } from "../../utils/api/WebSocket";
import { UserState } from "../../utils/helpers/types";
import styles from "./chat.module.scss";
import { ChatBotHistoryItem } from "./types";

export interface RecommendQuestionsProps {
  sendMessage: SendJsonMessage;
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
}

export default function CustomQuestions({
  sendMessage,
  setMessageHistory,
}: RecommendQuestionsProps) {
  const [showMoreQuestions, setShowMoreQuestions] = useState(true);
  const [questions, setQuestions] = useState<string[]>([]);
  const { queryWithWS } = useQueryWithTokens();
  const queryConfig = useSelector((state: UserState) => state.queryConfig);

  useEffect(() => {
    const data_profile = queryConfig?.selectedDataPro;
    if (data_profile) {
      getRecommendQuestions(data_profile).then((data) => {
        setQuestions(data);
      });
    }
  }, [queryConfig?.selectedDataPro]);

  const handleSendMessage = (question: string) => {
    // Call Fast API
    /*query({
      query: question,
      setLoading: setLoading,
      configuration: userState.queryConfig,
      setMessageHistory: setMessageHistory
    }).then();*/
    setShowMoreQuestions(true);
    // Call WebSocket API
    queryWithWS({
      query: question,
      sendMessage: sendMessage,
      setMessageHistory: setMessageHistory,
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
