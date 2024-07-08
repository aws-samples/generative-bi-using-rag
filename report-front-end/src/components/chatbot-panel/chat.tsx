import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { ChatBotHistoryItem, ChatBotMessageItem } from "./types";
import ChatInputPanel from "./chat-input-panel";
import { Box, SpaceBetween, Spinner, StatusIndicator } from "@cloudscape-design/components";
import ChatMessage from "./chat-message";
import styles from "./chat.module.scss";
import { createWssClient } from "../../common/api/WebSocket";
import { getSelectData } from "../../common/api/API";
import { useDispatch, useSelector } from "react-redux";
import { ActionType, LLMConfigState, UserState } from "../../common/helpers/types";

export default function Chat(
  props: {
    setToolsHide: Dispatch<SetStateAction<boolean>>;
  }) {

  const [messageHistory, setMessageHistory] = useState<ChatBotHistoryItem[]>([]);
  const [statusMessage, setStatusMessage] = useState<ChatBotMessageItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const sendJsonMessage = createWssClient(setStatusMessage, setMessageHistory);

  const dispatch = useDispatch();
  const userState = useSelector<UserState>((state) => state) as UserState;

  useEffect(() => {
    if (!userState.queryConfig.selectedLLM || !userState.queryConfig.selectedDataPro) {
      getSelectData().then(response => {
        if (response) {
          const configInfo: LLMConfigState = {
            ...userState.queryConfig,
            selectedLLM: response['bedrock_model_ids'][0],
            selectedDataPro: response['data_profiles'][0],
          };
          dispatch({ type: ActionType.UpdateConfig, state: configInfo });
        }
      });
    }
  }, [userState.queryConfig]);

  return (
    <div className={styles.chat_container}>
      <SpaceBetween size={'xxl'}>
        {messageHistory.map((message, idx) => {
            return (
              <div key={idx}>
                <ChatMessage
                  key={idx}
                  message={message}
                  setLoading={setLoading}
                  setMessageHistory={(history: SetStateAction<ChatBotHistoryItem[]>) => setMessageHistory(history)}
                  sendMessage={sendJsonMessage}
                />
              </div>
            );
          }
        )}
        <div className={styles.status_container}>
          <SpaceBetween size={'xxs'}>
            {statusMessage.map((message, idx) => {
              return (
                <StatusIndicator
                  key={idx}
                  type={message.content.status === "end" ? "success" : "in-progress"}>
                  {message.content.text}
                </StatusIndicator>
              );
            })
            }
          </SpaceBetween>
        </div>
        {loading && (
          <div>
            <Box float="left">
              <Spinner/>
            </Box>
          </div>
        )}
      </SpaceBetween>
      <div className={styles.welcome_text}>
        {messageHistory.length === 0 && statusMessage.length === 0 && !loading && (
          <center>{'GenBI Chatbot'}</center>
        )}
      </div>
      <div className={styles.input_container}>
        <ChatInputPanel
          setToolsHide={props.setToolsHide}
          setLoading={setLoading}
          messageHistory={messageHistory}
          setMessageHistory={(history: SetStateAction<ChatBotHistoryItem[]>) => setMessageHistory(history)}
          setStatusMessage={(message: SetStateAction<ChatBotMessageItem[]>) => setStatusMessage(message)}
          sendMessage={sendJsonMessage}
        />
      </div>
    </div>
  );
}
