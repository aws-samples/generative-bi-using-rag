import { Link, SpaceBetween } from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { Button } from "@aws-amplify/ui-react";
import { ChatBotHistoryItem, ChatInputState } from "./types";
import { BACKEND_URL } from "../../common/constant/constants";
import { useSelector } from "react-redux";
import { UserState } from "../config-panel/types";
import styles from "./chat.module.scss";
import { queryWithWS } from "../../common/api/WebSocket";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";

export interface RecommendQuestionsProps {
  setTextValue: Dispatch<SetStateAction<ChatInputState>>;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
  sendMessage: SendJsonMessage;
}

export default function CustomQuestions(props: RecommendQuestionsProps) {

  const [showMoreQuestions, setShowMoreQuestions] = useState(true);
  const [questions, setQuestions] = useState<string[]>([]);

  const userInfo = useSelector<UserState>((state) => state) as UserState;

  const getRecommendQuestions = async (data_profile: string) => {
    const url = `${BACKEND_URL}qa/get_custom_question?data_profile=${data_profile}`;
    console.log(url);
    try {
      const response = await fetch(url, {
        method: "GET",
      });
      if (!response.ok) {
        console.error("getCustomQuestions Error", response);
        return;
      }
      const result = await response.json();
      const custom_question = result['custom_question'];
      setQuestions(custom_question);
    } catch (error) {
      console.error("getCustomQuestions Error", error);
    }
  }

  useEffect(() => {
    const data_profile = userInfo.queryConfig.selectedDataPro;
    if (data_profile) {
      getRecommendQuestions(data_profile).then();
    }
  }, [userInfo.queryConfig.selectedDataPro]);

  const handleSendMessage = (question: string) => {
    // Call Fast API
    /*query({
      query: question,
      setLoading: props.setLoading,
      configuration: userInfo.queryConfig,
      setMessageHistory: props.setMessageHistory
    }).then();*/

    // Call WebSocket API
    queryWithWS({
      query: question,
      configuration: userInfo.queryConfig,
      sendMessage: props.sendMessage,
      setMessageHistory: props.setMessageHistory,
      userId: userInfo.userId
    });
  };

  return (
    <div>
      {questions.length > 0 && showMoreQuestions && (
        <SpaceBetween size={'xxs'}>
          <div className={styles.questions_grid}>
            {questions.slice(0, Math.min(3, questions.length)).map((question, kid) => (
              <Button
                key={kid}
                size="small"
                className={styles.button}
                onClick={() => handleSendMessage(question)}>
                {question}
              </Button>
            ))}
          </div>
          <div style={{float: 'right'}}>
            <Link
              variant="primary"
              onFollow={
                () => setShowMoreQuestions(false)
              }>
              <p className={styles.text}>More sample suggestions</p>
            </Link>
          </div>
        </SpaceBetween>
      )}
      {questions.length > 0 && !showMoreQuestions && (
        <SpaceBetween size={'xxs'}>
          <div className={styles.questions_grid}>
            {questions.map((question, kid) => (
              <Button
                key={kid}
                size="small"
                className={styles.button}
                onClick={() => handleSendMessage(question)}>
                {question}
              </Button>
            ))}
          </div>
          <div
            style={{float: 'right'}}>
            <Link
              variant="primary"
              onFollow={
                () => setShowMoreQuestions(true)
              }>
              <p className={styles.text}>Less sample suggestions</p>
            </Link>
          </div>
        </SpaceBetween>
      )}
    </div>
  );
}