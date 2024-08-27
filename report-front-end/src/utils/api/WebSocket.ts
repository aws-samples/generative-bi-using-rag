import { Dispatch, SetStateAction, useCallback } from "react";
import useWebSocket from "react-use-websocket";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import {
  ChatBotHistoryItem,
  ChatBotMessageItem,
  ChatBotMessageType,
} from "../../components/SectionChat/types";
import { Session } from "../../components/PanelSideNav/types";
import { DEFAULT_QUERY_CONFIG, isLoginWithCognito } from "../constants";
import { logout } from "../helpers/tools";
import { getBearerTokenObj } from "./API";
import { useSelector } from "react-redux";
import { UserState } from "../helpers/types";
import useGlobalContext from "../../hooks/useGlobalContext";

export function useCreateWssClient(
  setStatusMessage: Dispatch<SetStateAction<ChatBotMessageItem[]>>,
  setSessions: Dispatch<SetStateAction<Session[]>>
) {
  const socketUrl = process.env.VITE_WEBSOCKET_URL as string;
  const { sendJsonMessage } = useWebSocket(socketUrl, {
    onOpen: (openMessage) =>
      console.log("websocket connection opened, ", openMessage),
    onClose: (closeMessage) =>
      console.error("websocket connection closed, ", closeMessage),
    onError: (errorMessage) =>
      console.error("websocket connection error, ", errorMessage),
    //Will attempt to reconnect on all close events, such as server shutting down
    shouldReconnect: () => true,
    onMessage: (message) => handleWebSocketMessage(message),
  });

  const handleWebSocketMessage = (message: MessageEvent) => {
    console.log("Received WebSocketMessage: ", message.data);
    const messageJson = JSON.parse(message.data);

    if (isLoginWithCognito) {
      if (messageJson.content["X-Status-Code"] === 401) {
        return logout();
      } else if (messageJson.content["X-Status-Code"] === 200) {
        // Do something extra here
      }
    }

    if (messageJson.content_type === "state") {
      setStatusMessage((historyMessage) => [...historyMessage, messageJson]);
    } else {
      setStatusMessage([]);
      setSessions((prevList) => {
        return prevList.map((item) => {
          if (messageJson.session_id !== item.session_id) {
            return item;
          } else {
            return {
              session_id: item.session_id,
              title: item.title,
              messages: [
                ...item.messages,
                {
                  type: ChatBotMessageType.AI,
                  content: messageJson.content,
                },
              ],
            };
          }
        });
      });
    }
  };

  return sendJsonMessage;
}

export const useQueryWithTokens = () => {
  const userInfo = useSelector((state: UserState) => state.userInfo);
  const queryConfig = useSelector((state: UserState) => state.queryConfig);
  const globalContext = useGlobalContext();
  const { currentSessionId, setSessions } = globalContext;

  const queryWithWS = useCallback(
    (props: {
      query: string;
      sendJsonMessage: SendJsonMessage;
      setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
    }) => {
      setSessions((prevList) => {
        return prevList.map((item) => {
          if (currentSessionId !== item.session_id) return item;
          return {
            ...item,
            title: item.title === "New Chat" ? props.query : item.title,
            messages: item.messages.concat({
              type: ChatBotMessageType.Human,
              content: props.query,
            }),
          };
        });
      });
      const extraToken = isLoginWithCognito ? getBearerTokenObj() : {};
      const param = {
        query: props.query,
        bedrock_model_id:
          queryConfig.selectedLLM || DEFAULT_QUERY_CONFIG.selectedLLM,
        use_rag_flag: true,
        visualize_results_flag: true,
        intent_ner_recognition_flag: queryConfig.intentChecked,
        agent_cot_flag: queryConfig.complexChecked,
        profile_name:
          queryConfig.selectedDataPro || DEFAULT_QUERY_CONFIG.selectedDataPro,
        explain_gen_process_flag: true,
        gen_suggested_question_flag: queryConfig.modelSuggestChecked,
        answer_with_insights:
          queryConfig.answerInsightChecked ||
          DEFAULT_QUERY_CONFIG.answerInsightChecked,
        top_k: queryConfig.topK,
        top_p: queryConfig.topP,
        max_tokens: queryConfig.maxLength,
        temperature: queryConfig.temperature,
        context_window: queryConfig.contextWindow,
        session_id: currentSessionId,
        user_id: userInfo.userId,
        username: userInfo.username,
        ...extraToken,
      };
      console.log("Send WebSocketMessage: ", param);
      props.sendJsonMessage(param);
    },
    [
      currentSessionId,
      queryConfig.answerInsightChecked,
      queryConfig.complexChecked,
      queryConfig.contextWindow,
      queryConfig.intentChecked,
      queryConfig.maxLength,
      queryConfig.modelSuggestChecked,
      queryConfig.selectedDataPro,
      queryConfig.selectedLLM,
      queryConfig.temperature,
      queryConfig.topK,
      queryConfig.topP,
      setSessions,
      userInfo.userId,
      userInfo.username,
    ]
  );
  return { queryWithWS, userInfo, queryConfig, ...globalContext };
};
