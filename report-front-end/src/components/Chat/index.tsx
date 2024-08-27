import {
  Box,
  SpaceBetween,
  Spinner,
  StatusIndicator,
} from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { getHistoryBySession, getSelectData } from "../../utils/api/API";
import { useCreateWssClient } from "../../utils/api/WebSocket";
import {
  ActionType,
  LLMConfigState,
  UserState,
} from "../../utils/helpers/types";
import useGlobalContext from "../../hooks/useGlobalContext";
import ChatInput from "./ChatInput";
import MessageRenderer from "./MessageRenderer";
import styles from "./chat.module.scss";
import { ChatBotHistoryItem, ChatBotMessageItem } from "./types";

export default function Chat({
  setToolsHide,
  toolsHide,
}: {
  setToolsHide: Dispatch<SetStateAction<boolean>>;
  toolsHide: boolean;
}) {
  const [messageHistory, setMessageHistory] = useState<ChatBotHistoryItem[]>(
    []
  );
  const [statusMessage, setStatusMessage] = useState<ChatBotMessageItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const { sessions, setSessions, currentSessionId, setCurrentSessionId } =
    useGlobalContext();
  const sendJsonMessage = useCreateWssClient(setStatusMessage, setSessions);
  console.log({ sessions, messageHistory });

  const dispatch = useDispatch();
  const queryConfig = useSelector((state: UserState) => state.queryConfig);
  const userInfo = useSelector((state: UserState) => state.userInfo);

  useEffect(() => {
    if (!queryConfig.selectedLLM || !queryConfig.selectedDataPro) {
      getSelectData().then((response) => {
        if (response) {
          if (!queryConfig.selectedLLM && response["bedrock_model_ids"]) {
            const configInfo: LLMConfigState = {
              ...queryConfig,
              selectedLLM:
                response["bedrock_model_ids"].length > 0
                  ? response["bedrock_model_ids"][0]
                  : queryConfig.selectedLLM,
            };
            dispatch({ type: ActionType.UpdateConfig, state: configInfo });
          } else if (
            !queryConfig.selectedDataPro &&
            response["data_profiles"]
          ) {
            const configInfo: LLMConfigState = {
              ...queryConfig,
              selectedDataPro:
                response["data_profiles"].length > 0
                  ? response["data_profiles"][0]
                  : queryConfig.selectedDataPro,
            };
            dispatch({ type: ActionType.UpdateConfig, state: configInfo });
          }
        }
      });
    }
  }, [queryConfig]);

  useEffect(() => {
    sessions.forEach((session) => {
      if (session.session_id === currentSessionId) {
        setMessageHistory(session.messages);
        if (session.messages?.length === 0 && session.title !== "New Chat") {
          const historyItem = {
            session_id: session.session_id,
            user_id: userInfo.userId,
            profile_name: queryConfig.selectedDataPro,
          };
          getHistoryBySession(historyItem).then((response) => {
            if (response) {
              setSessions((prevState) => {
                return prevState.map((session) => {
                  if (response.session_id !== session.session_id) {
                    return session;
                  } else {
                    return {
                      session_id: session.session_id,
                      title: session.title,
                      messages: response.messages,
                    };
                  }
                });
              });
            }
          });
        }
      }
    });
  }, [currentSessionId]);

  useEffect(() => {
    sessions.forEach((session) => {
      if (session.session_id === currentSessionId) {
        setMessageHistory(session.messages);
      }
    });
  }, [sessions]);

  return (
    <div className={styles.chat_container}>
      <SpaceBetween size="xxs">
        {messageHistory?.map((message, idx) => {
          return (
            <div key={idx}>
              <MessageRenderer
                key={idx}
                message={message}
                setMessageHistory={(
                  history: SetStateAction<ChatBotHistoryItem[]>
                ) => setMessageHistory(history)}
                sendMessage={sendJsonMessage}
              />
            </div>
          );
        })}
        {statusMessage?.filter(
          (status) => status.session_id === currentSessionId
        ).length === 0 ? null : (
          <div className={styles.status_container}>
            <SpaceBetween size="xxs">
              {statusMessage
                .filter((status) => status.session_id === currentSessionId)
                .map((message, idx) => {
                  const displayMessage =
                    idx % 2 === 1 ? true : idx === statusMessage.length - 1;
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
          <div className={styles.status_container}>
            <Box float="left">
              <Spinner />
            </Box>
          </div>
        )}
      </SpaceBetween>
      <div className={styles.welcome_text}>
        {messageHistory?.length === 0 &&
          statusMessage?.length === 0 &&
          !loading && <center>{"GenBI Chatbot"}</center>}
      </div>
      <div className={styles.input_container}>
        <ChatInput
          setToolsHide={setToolsHide}
          toolsHide={toolsHide}
          setLoading={setLoading}
          messageHistory={messageHistory}
          setMessageHistory={(history: SetStateAction<ChatBotHistoryItem[]>) =>
            setMessageHistory(history)
          }
          sessions={sessions}
          setSessions={setSessions}
          setStatusMessage={(message: SetStateAction<ChatBotMessageItem[]>) =>
            setStatusMessage(message)
          }
          sendMessage={sendJsonMessage}
          currSessionId={currentSessionId}
          setCurrentSessionId={setCurrentSessionId}
        />
      </div>
    </div>
  );
}
