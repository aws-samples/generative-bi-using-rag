import { Link, SpaceBetween } from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useState } from "react";
import { Button } from "@aws-amplify/ui-react";
import styles from "../../styles/chat.module.scss";
import data from "../../mockdata/questions.json"
import { ChatInputState } from "./types";

export interface RecommendQuestionsProps {
    setTextValue: Dispatch<SetStateAction<ChatInputState>>;
}

export default function RecommendQuestions(props: RecommendQuestionsProps) {

    console.log(data);
    const [showMoreQuestions, setShowMoreQuestions] = useState(true);
    const [questions, setQuestions] = useState<string[]>(data.slice(0, 3));

    // todo：get recommended questions

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
                                setQuestions(data.slice(0, 3));
                            }
                        }>
                        Show less suggestions
                    </Link>
                </div>
            )}
        </SpaceBetween>
    );
}