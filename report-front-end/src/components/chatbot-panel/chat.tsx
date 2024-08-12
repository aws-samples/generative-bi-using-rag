import { Box, SpaceBetween, Spinner, StatusIndicator } from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { getSelectData } from "../../common/api/API";
import { createWssClient } from "../../common/api/WebSocket";
import { ActionType, LLMConfigState, UserState } from "../../common/helpers/types";
import ChatInputPanel from "./chat-input-panel";
import ChatMessage from "./chat-message";
import styles from "./chat.module.scss";
import { ChatBotHistoryItem, ChatBotMessageItem } from "./types";
import { Session } from "../session-panel/types";

export default function Chat(props: {
  setToolsHide: Dispatch<SetStateAction<boolean>>;
  toolsHide: boolean;
  sessions: Session[];
  setSessions: Dispatch<SetStateAction<Session[]>>;
  currentSessionId: string;
}) {
  const [messageHistory, setMessageHistory] = useState<ChatBotHistoryItem[]>(
    [],
  );
  const [statusMessage, setStatusMessage] = useState<ChatBotMessageItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const sendJsonMessage = createWssClient(setStatusMessage, props.setSessions);

  const dispatch = useDispatch();
  const userState = useSelector<UserState>((state) => state) as UserState;

  useEffect(() => {
    if (
      !userState.queryConfig.selectedLLM ||
      !userState.queryConfig.selectedDataPro
    ) {
      getSelectData().then((response: any) => {
        if (response) {
          if (!userState.queryConfig.selectedLLM && response["bedrock_model_ids"]) {
            const configInfo: LLMConfigState = {
              ...userState.queryConfig,
              selectedLLM: response["bedrock_model_ids"].length > 0 ? response["bedrock_model_ids"][0] : userState.queryConfig.selectedLLM,
            };
            dispatch({ type: ActionType.UpdateConfig, state: configInfo });
          } else if (!userState.queryConfig.selectedDataPro && response["data_profiles"]) {
            const configInfo: LLMConfigState = {
              ...userState.queryConfig,
              selectedDataPro: response["data_profiles"].length > 0 ? response["data_profiles"][0] : userState.queryConfig.selectedDataPro,
            };
            dispatch({ type: ActionType.UpdateConfig, state: configInfo });
          }
        }
      });
    }
  }, [userState.queryConfig]);

  useEffect(() => {
    props.sessions.forEach((session) => {
      if (session.session_id === props.currentSessionId) {
        setMessageHistory(session.messages);
      }
    });
  }, [props.currentSessionId]);

  useEffect(() => {
    props.sessions.forEach((session) => {
      if (session.session_id === props.currentSessionId) {
        setMessageHistory(session.messages);
      }
    });
  }, [props.sessions]);

  return (
    <div className={styles.chat_container}>
      <SpaceBetween size="xxs">
        {messageHistory.map((message, idx) => {
          return (
            <div key={idx}>
              <ChatMessage
                key={idx}
                message={message}
                setLoading={setLoading}
                setMessageHistory={(
                  history: SetStateAction<ChatBotHistoryItem[]>,
                ) => setMessageHistory(history)}
                setSessions={props.setSessions}
                sendMessage={sendJsonMessage}
                sessionId={props.currentSessionId}
              />
            </div>
          );
        })}
        {statusMessage.filter((status) => status.session_id === props.currentSessionId).length === 0 ?
          null : (<div className={styles.status_container}>
              <SpaceBetween size="xxs">
                {statusMessage.filter((status) => status.session_id === props.currentSessionId)
                  .map((message, idx) => {
                    const displayMessage =
                      idx % 2 === 1
                        ? true
                        : idx === statusMessage.length - 1;
                    return displayMessage ? (
                      <StatusIndicator
                        key={idx}
                        type={
                          message.content.status === "end"
                            ? "success"
                            : "in-progress"
                        }
                      >
                        {message.content.text}
                      </StatusIndicator>
                    ) : null;
                  })}
              </SpaceBetween>
            </div>
          )}

        {loading && (
          <div>
            <Box float="left">
              <Spinner />
            </Box>
          </div>
        )}
      </SpaceBetween>
      <div className={styles.welcome_text}>
        {messageHistory.length === 0 &&
          statusMessage.filter((status) => status.session_id === props.currentSessionId).length === 0 &&
          !loading && <center>{"GenBI Chatbot"}</center>}
      </div>
      <div className={styles.input_container}>
        <ChatInputPanel
          setToolsHide={props.setToolsHide}
          toolsHide={props.toolsHide}
          setLoading={setLoading}
          messageHistory={messageHistory}
          setMessageHistory={(history: SetStateAction<ChatBotHistoryItem[]>) =>
            setMessageHistory(history)
          }
          setSessions={props.setSessions}
          setStatusMessage={(message: SetStateAction<ChatBotMessageItem[]>) =>
            setStatusMessage(message)
          }
          sendMessage={sendJsonMessage}
          currSessionId={props.currentSessionId}
        />
      </div>
    </div>
  );
}
