import { Button, Container, Icon, SpaceBetween, Spinner, } from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState, } from "react";
import TextareaAutosize from "react-textarea-autosize";
import styles from "../../styles/chat.module.scss";
import { ChatBotConfiguration, ChatInputState, } from "./types";
import RecommendQuestions from "./recommend-questions";

export interface ChatInputPanelProps {
    running: boolean;
    setRunning: Dispatch<SetStateAction<boolean>>;
    configuration: ChatBotConfiguration;
    setConfiguration: Dispatch<SetStateAction<ChatBotConfiguration>>;
}

export abstract class ChatScrollState {
    static userHasScrolled = false;
    static skipNextScrollEvent = false;
    static skipNextHistoryUpdate = false;
}

export default function ChatInputPanel(props: ChatInputPanelProps) {
    const [state, setTextValue] = useState<ChatInputState>({
        value: ""
    });

    useEffect(() => {
        const onWindowScroll = () => {
            if (ChatScrollState.skipNextScrollEvent) {
                ChatScrollState.skipNextScrollEvent = false;
                return;
            }

            const isScrollToTheEnd =
                Math.abs(
                    window.innerHeight +
                    window.scrollY -
                    document.documentElement.scrollHeight
                ) <= 10;

            ChatScrollState.userHasScrolled = !isScrollToTheEnd;
        };

        window.addEventListener("scroll", onWindowScroll);

        return () => {
            window.removeEventListener("scroll", onWindowScroll);
        };
    }, []);

    useEffect(() => {
        // todo:
    }, [props.configuration]);

    const handleSendMessage = () => {
        // todo: handle send message
        console.log('handleSendMessage');
    };

    return (
        <SpaceBetween direction="vertical" size="l">
            <div className={styles.input_area_container}>
                <Container>
                    <SpaceBetween size={'s'}>
                        <RecommendQuestions setTextValue={setTextValue}></RecommendQuestions>
                        <div className={styles.input_textarea_container}>
                            <SpaceBetween size="xxs" direction="horizontal" alignItems="center">
                                <Icon name="microphone" variant="disabled"/>
                            </SpaceBetween>
                            <TextareaAutosize
                                className={styles.input_textarea}
                                maxRows={6}
                                minRows={1}
                                spellCheck={true}
                                autoFocus
                                onChange={(e) =>
                                    setTextValue((state) => ({...state, value: e.target.value}))
                                }
                                onKeyDown={(e) => {
                                    if (e.key == "Enter" && !e.shiftKey) {
                                        e.preventDefault();
                                        handleSendMessage();
                                    }
                                }}
                                value={state.value}
                                placeholder={"Send a message"}
                            />
                            <div style={{marginLeft: "8px"}}>
                                <Button
                                    onClick={handleSendMessage}
                                    iconAlign="right"
                                    iconName={!props.running ? "angle-right-double" : undefined}
                                    variant="primary"
                                >
                                    {props.running ? (
                                        <>
                                            Loading&nbsp;&nbsp;
                                            <Spinner/>
                                        </>
                                    ) : (
                                        "Send"
                                    )}
                                </Button>
                                <Button
                                    iconName="settings"
                                    variant="icon"
                                />
                            </div>
                        </div>
                    </SpaceBetween>
                </Container>
                {/*<StatusIndicator type={"success"}>
                    {"Connected"}
                </StatusIndicator>*/}
            </div>
        </SpaceBetween>
    );
}