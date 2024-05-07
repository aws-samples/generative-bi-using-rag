import { Link, SpaceBetween } from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { Button } from "@aws-amplify/ui-react";
import styles from "../../styles/chat.module.scss";
import data from "../../mockdata/questions.json"
import { ChatInputState } from "./types";

export interface RecommendQuestionsProps {
  setTextValue: Dispatch<SetStateAction<ChatInputState>>;
}

export default function RecommendQuestions(props: RecommendQuestionsProps) {

  // console.log(data);
  const [showMoreQuestions, setShowMoreQuestions] = useState(true);
  const [questions, setQuestions] = useState<string[]>(data.slice(0, Math.min(3, data.length)));

  // const [questions, setQuestions] = useState<string[]>([]);

  function getRecommendQuestions() {
    const endpoint = "http://54.187.192.177:8000";
    const url = `${endpoint}/qa/get_custom_question?data_profile=shopping-demo`;
    fetch(url, {
      method: 'GET',
      mode: "no-cors"
    })
      .then(res => {
        console.log(res);
        if (!res.ok) {
          throw new Error('Network response was not ok');
        }
        return res.json();
      })
      .then(data => {
        console.log(data);
        // todo：set recommended questions
        // setQuestions(data);
      })
      .catch(err => {
        console.log(err);
      });
  }

  useEffect(() => {
    console.log('fetch data');
    // getRecommendQuestions();
  }, []);

  return (
    <SpaceBetween size={'xxs'}>
      <div className={styles.questions_grid}>
        {questions.map(question => (
          <Button
            className={styles.button_border}
            onClick={() => props.setTextValue({value: question})}>
            {question}
          </Button>
        ))}
      </div>
      {showMoreQuestions && (
        <div
          style={{float: 'right'}}>
          <Link
            variant="primary"
            onFollow={
              () => {
                setShowMoreQuestions(false);
                setQuestions(data);
              }
            }>
            Show more suggestions
          </Link>
        </div>
      )}
      {!showMoreQuestions && (
        <div
          style={{float: 'right'}}>
          <Link
            variant="primary"
            onFollow={
              () => {
                setShowMoreQuestions(true);
                setQuestions(data.slice(0, Math.min(3, data.length)));
              }
            }>
            Show less suggestions
          </Link>
        </div>
      )}
    </SpaceBetween>
  );
}