import { LoadingBar } from "@cloudscape-design/chat-components";
import {
  Box,
  SpaceBetween,
  Spinner,
  StatusIndicator,
} from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import useGlobalContext from "../../hooks/useGlobalContext";
import { getHistoryBySession, getSelectData } from "../../utils/api/API";
import { useCreateWssClient } from "../../utils/api/WebSocket";
import {
  ActionType,
  LLMConfigState,
  UserState,
} from "../../utils/helpers/types";
import ChatInput from "./ChatInput";
import MessageRenderer from "./MessageRenderer";
import styles from "./chat.module.scss";
import { ChatBotHistoryItem, ChatBotMessageItem } from "./types";

export default function SectionChat({
  setToolsHide,
  toolsHide,
}: {
  setToolsHide: Dispatch<SetStateAction<boolean>>;
  toolsHide: boolean;
}) {
  const [messageHistory, setMessageHistory] = useState<ChatBotHistoryItem[]>(
    []
  );
  const [isLoadingSessionHistory, setIsLoadingSessionHistory] = useState(false);

  const [statusMessage, setStatusMessage] = useState<ChatBotMessageItem[]>([]);
  const { sessions, setSessions, currentSessionId, isSearching } =
    useGlobalContext();

  const sendJsonMessage = useCreateWssClient(setStatusMessage);

  const dispatch = useDispatch();
  const queryConfig = useSelector((state: UserState) => state.queryConfig);
  const userInfo = useSelector((state: UserState) => state.userInfo);

  useEffect(() => {
    if (!queryConfig.selectedLLM || !queryConfig.selectedDataPro) {
      getSelectData().then((response) => {
        if (!response) return;
        if (!queryConfig.selectedLLM && response.bedrock_model_ids?.length) {
          const configInfo: LLMConfigState = {
            ...queryConfig,
            selectedLLM: response.bedrock_model_ids[0],
          };
          dispatch({ type: ActionType.UpdateConfig, state: configInfo });
        } else if (
          !queryConfig.selectedDataPro &&
          response.data_profiles?.length
        ) {
          const configInfo: LLMConfigState = {
            ...queryConfig,
            selectedDataPro: response.data_profiles[0],
          };
          dispatch({ type: ActionType.UpdateConfig, state: configInfo });
        }
      });
    }
  }, [dispatch, queryConfig]);

  useEffect(() => {
    setIsLoadingSessionHistory(true);
    getHistoryBySession({
      session_id: currentSessionId,
      user_id: userInfo.userId,
      profile_name: queryConfig.selectedDataPro,
    })
      .then((data) => {
        if (!data) return;
        const { messages, session_id } = data;
        setSessions((prevList) => {
          return prevList.map((item) => {
            if (session_id === item.session_id) {
              setMessageHistory(messages);
              return { ...item, messages };
            }
            return session_id === item.session_id
              ? { ...item, messages }
              : item;
          });
        });
      })
      .finally(() => {
        setIsLoadingSessionHistory(false);
      });
  }, [
    currentSessionId,
    queryConfig.selectedDataPro,
    setSessions,
    userInfo.userId,
  ]);

  useEffect(() => {
    sessions.forEach((session) => {
      if (session.session_id === currentSessionId) {
        setMessageHistory(session.messages);
      }
    });
  }, [currentSessionId, sessions]);

  return (
    <section className={styles.chat_container}>
      <SpaceBetween size="xxs">
        {isLoadingSessionHistory ? (
          <Box variant="h3" margin="xxl" padding="xxl">
            <Spinner /> Loading latest chat records...
          </Box>
        ) : (
          <>
            {messageHistory?.map((message, idx) => {
              return (
                <div key={idx}>
                  <MessageRenderer
                    key={idx}
                    message={message}
                    setMessageHistory={setMessageHistory}
                    sendJsonMessage={sendJsonMessage}
                  />
                </div>
              );
            })}

            {!isSearching ? null : (
              <div className={styles.status_container}>
                <div style={{ position: "absolute", top: 0, width: "100%" }}>
                  <LoadingBar variant="gen-ai-masked" />
                </div>
                <SpaceBetween size="xxs">
                  {statusMessage?.length ? (
                    statusMessage.map((message, idx) => {
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
                    })
                  ) : (
                    <Spinner />
                  )}
                </SpaceBetween>
              </div>
            )}
          </>
        )}
      </SpaceBetween>

      <div className={styles.welcome_text}>
        {messageHistory?.length === 0 &&
          statusMessage?.length === 0 &&
          !isLoadingSessionHistory && <center>GenBI Chatbot</center>}
      </div>

      <div className={styles.input_container}>
        <ChatInput
          toolsHide={toolsHide}
          setToolsHide={setToolsHide}
          messageHistory={messageHistory}
          setStatusMessage={setStatusMessage}
          sendJsonMessage={sendJsonMessage}
        />
      </div>
    </section>
  );
}
