import { useState } from "react";
import { ChatBotConfiguration, ChatBotHistoryItem, ChatBotMessageType, } from "./types";
import ChatInputPanel from "./chat-input-panel";
import styles from "../../styles/chat.module.scss";
import { SpaceBetween } from "@cloudscape-design/components";
import ChatMessage from "./chat-message";

export default function Chat() {
    const [running, setRunning] = useState<boolean>(false);
    const [configuration, setConfiguration] = useState<ChatBotConfiguration>(
        () => ({
            streaming: true,
            showMetadata: false,
            maxTokens: 512,
            temperature: 0.6,
            topP: 0.9,
            files: null,
        })
    );

    const [messageHistory, setMessageHistory] = useState<ChatBotHistoryItem[]>(
        []
    );

    return (
        <div className={styles.chat_container}>
            <SpaceBetween size={'s'}>
                {/*{messageHistory.map((message, idx) => (
                    <ChatMessage
                        message={message}
                        onThumbsUp={() => {
                        }}
                        onThumbsDown={() => {
                        }}/>
                ))}*/}
                <ChatMessage
                    message={{
                        type: ChatBotMessageType.Human,
                        content: "帮我分析一下商品的销售情况"}}
                    onThumbsUp={() => {
                    }}
                    onThumbsDown={() => {
                    }}/>
            </SpaceBetween>
            {/*<div className={styles.welcome_text}>
                <center>{'GenBI Chatbot'}</center>
            </div>*/}
            <div className={styles.input_container}>
                <ChatInputPanel
                    running={running}
                    setRunning={setRunning}
                    configuration={configuration}
                    setConfiguration={setConfiguration}
                />
            </div>
        </div>
    );
}
