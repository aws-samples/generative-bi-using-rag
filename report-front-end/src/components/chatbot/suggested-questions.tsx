import { Button } from "@aws-amplify/ui-react";
import styles from "../../styles/chat.module.scss";

export interface SuggestedQuestionsProps {
  questions: string[];
}

export default function SuggestedQuestions(props: SuggestedQuestionsProps) {

  return (
    <div className={styles.questions_grid}>
      {props.questions.map((question, kid) => (
        <Button
          key={kid}
          onClick={() => {}}>
          {question}
        </Button>
      ))}
    </div>
  );
}