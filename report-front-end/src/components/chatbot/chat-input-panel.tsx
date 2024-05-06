import {
    Button,
    Container,
    Icon,
    SelectProps,
    SpaceBetween,
    Spinner,
    StatusIndicator,
} from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState, } from "react";
// @ts-ignore
import { useSpeechRecognition } from "react-speech-recognition";
import TextareaAutosize from "react-textarea-autosize";
import styles from "../../styles/chat.module.scss";
import { ChatBotConfiguration, ChatInputState, } from "./types";

export interface ChatInputPanelProps {
    running: boolean;
    setRunning: Dispatch<SetStateAction<boolean>>;
    configuration: ChatBotConfiguration;
    setConfiguration: Dispatch<React.SetStateAction<ChatBotConfiguration>>;
}

export abstract class ChatScrollState {
    static userHasScrolled = false;
    static skipNextScrollEvent = false;
    static skipNextHistoryUpdate = false;
}

const workspaceDefaultOptions: SelectProps.Option[] = [
    {
        label: "No workspace (RAG data source)",
        value: "",
        iconName: "close",
    },
    {
        label: "Create new workspace",
        value: "__create__",
        iconName: "add-plus",
    },
];

export default function ChatInputPanel(props: ChatInputPanelProps) {
    const {transcript, listening, browserSupportsSpeechRecognition} =
        useSpeechRecognition();
    const [state, setState] = useState<ChatInputState>({
        value: ""
    });

    useEffect(() => {
        if (transcript) {
            setState((state) => ({...state, value: transcript}));
        }
    }, [transcript]);

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

            if (!isScrollToTheEnd) {
                ChatScrollState.userHasScrolled = true;
            } else {
                ChatScrollState.userHasScrolled = false;
            }
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
    };

    /*  const connectionStatus = {
        [ReadyState.CONNECTING]: "Connecting",
        [ReadyState.OPEN]: "Open",
        [ReadyState.CLOSING]: "Closing",
        [ReadyState.CLOSED]: "Closed",
        [ReadyState.UNINSTANTIATED]: "Uninstantiated",
      }[readyState];*/

    return (
        <SpaceBetween direction="vertical" size="l">
            <div className={styles.input_area_container}>
                <Container>
                    <div className={styles.input_textarea_container}>
                        <SpaceBetween size="xxs" direction="horizontal" alignItems="center">
                            {browserSupportsSpeechRecognition ? (
                                <Button
                                    iconName={listening ? "microphone-off" : "microphone"}
                                    variant="icon"
                                    onClick={() => {
                                    }}
                                />
                            ) : (
                                <Icon name="microphone-off" variant="disabled"/>
                            )}
                        </SpaceBetween>
                        <TextareaAutosize
                            className={styles.input_textarea}
                            maxRows={6}
                            minRows={1}
                            spellCheck={true}
                            autoFocus
                            onChange={(e) =>
                                setState((state) => ({...state, value: e.target.value}))
                            }
                            onKeyDown={(e) => {
                                if (e.key == "Enter" && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSendMessage();
                                }
                            }}
                            value={state.value}
                            placeholder={listening ? "Listening..." : "Send a message"}
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
                </Container>
                <StatusIndicator
                    type={"success"}
                >
                    {"Connected"}
                </StatusIndicator>
            </div>
            <div className={styles.input_controls}>
                <div className={styles.input_controls_right}>
                    <SpaceBetween direction="horizontal" size="xxs" alignItems="center">
                        <div style={{paddingTop: "1px"}}>
                        </div>
                    </SpaceBetween>
                </div>
            </div>
        </SpaceBetween>
    );
}