import { Button } from "@aws-amplify/ui-react";
import styles from "./chat.module.scss";

export interface SuggestedQuestionsProps {
  questions: string[];
}

export default function SuggestedQuestions(props: SuggestedQuestionsProps) {

  const handleQuery = () => {
  };

  return (
    <div className={styles.questions_grid}>
      {props.questions.map((question, kid) => (
        <Button
          key={kid}
          className={styles.button_border}
          onClick={handleQuery}>
          {question}
        </Button>
      ))}
    </div>
  );
}