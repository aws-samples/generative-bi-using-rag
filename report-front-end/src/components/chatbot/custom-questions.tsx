import { Link, SpaceBetween } from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { Button } from "@aws-amplify/ui-react";
import styles from "../../styles/chat.module.scss";
import { ChatInputState } from "./types";
import { BACKEND_URL } from "../../tools/const";

export interface RecommendQuestionsProps {
  setTextValue: Dispatch<SetStateAction<ChatInputState>>;
}

export default function CustomQuestions(props: RecommendQuestionsProps) {

  const [showMoreQuestions, setShowMoreQuestions] = useState(true);
  const [questions, setQuestions] = useState<string[]>([]);

  const getRecommendQuestions = async () => {
    const url = `${BACKEND_URL}qa/get_custom_question?data_profile=shopping-demo`;
    const response = await fetch(url, {
      method: "GET",
    });
    if (!response.ok) {
      return;
    }
    const result = await response.json();
    const custom_question = result['custom_question'];
    setQuestions(custom_question);
  }

  useEffect(() => {
    getRecommendQuestions().then();
  }, []);

  return (
    <div>
      {questions.length > 0 && showMoreQuestions && (
        <SpaceBetween size={'xxs'}>
          <div className={styles.questions_grid}>
            {questions.slice(0, Math.min(3, questions.length)).map((question, kid) => (
              <Button
                key={kid}
                className={styles.button_border}
                onClick={() => props.setTextValue({value: question})}>
                {question}
              </Button>
            ))}
          </div>
          <div
            style={{float: 'right'}}>
            <Link
              variant="primary"
              onFollow={
                () => setShowMoreQuestions(false)
              }>
              Show more suggestions
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
                className={styles.button_border}
                onClick={() => props.setTextValue({value: question})}>
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
              Show less suggestions
            </Link>
          </div>
        </SpaceBetween>
      )}
    </div>
  );
}