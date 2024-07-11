import { Link, SpaceBetween } from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { Button } from "@aws-amplify/ui-react";
import { ChatBotHistoryItem, ChatInputState } from "./types";
import { BACKEND_URL } from "../../common/constant/constants";
import { useSelector } from "react-redux";
import styles from "./chat.module.scss";
import { queryWithWS } from "../../common/api/WebSocket";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import { UserState } from "../../common/helpers/types";
import request from "umi-request";

export interface RecommendQuestionsProps {
  setTextValue: Dispatch<SetStateAction<ChatInputState>>;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
  sendMessage: SendJsonMessage;
}

export default function CustomQuestions(props: RecommendQuestionsProps) {

  const [showMoreQuestions, setShowMoreQuestions] = useState(true);
  const [questions, setQuestions] = useState<string[]>([]);

  const userState = useSelector<UserState>((state) => state) as UserState;

  const getRecommendQuestions = async (data_profile: string) => {
    try {
      request.get(`${BACKEND_URL}qa/get_custom_question?data_profile=${data_profile}`, {
        timeout: 3000,
      }).then((response: any) => {
        if (response) {
          const custom_question = response['custom_question'];
          setQuestions(custom_question);
        }
      });
    } catch (error) {
      console.error("getCustomQuestions Error", error);
    }
  }

  useEffect(() => {
    const data_profile = userState.queryConfig?.selectedDataPro;
    if (data_profile) {
      getRecommendQuestions(data_profile).then();
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
    setShowMoreQuestions(true)
    // Call WebSocket API
    queryWithWS({
      query: question,
      configuration: userState.queryConfig,
      sendMessage: props.sendMessage,
      setMessageHistory: props.setMessageHistory,
      userId: userState.userInfo.userId
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
