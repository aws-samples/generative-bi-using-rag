import { Dispatch, SetStateAction, useCallback } from "react";
import useWebSocket from "react-use-websocket";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import {
  ChatBotHistoryItem,
  ChatBotMessageItem,
  ChatBotMessageType,
} from "../../components/chatbot-panel/types";
import { Session } from "../../components/session-panel/types";
import {
  DEFAULT_QUERY_CONFIG,
  isLoginWithCognito,
} from "../constant/constants";
import { logout } from "../helpers/tools";
import { getBearerTokenObj } from "./API";

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
      setSessions((prevState) => {
        return prevState.map((session) => {
          if (messageJson.session_id !== session.session_id) {
            return session;
          } else {
            return {
              session_id: session.session_id,
              title: session.title,
              messages: [
                ...session.messages,
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

export const useQueryWithCookies = () => {
  const queryWithWS = useCallback(
    (props: {
      query: string;
      configuration: any;
      sendMessage: SendJsonMessage;
      setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
      setSessions: Dispatch<SetStateAction<Session[]>>;
      userId: string;
      username: string;
      sessionId: string;
    }) => {
      props.setSessions((prevState) => {
        return prevState.map((session: Session) => {
          if (props.sessionId !== session.session_id) {
            return session;
          } else {
            return {
              session_id: session.session_id,
              title: session.title === "New Chat" ? props.query : session.title,
              messages: [
                ...session.messages,
                {
                  type: ChatBotMessageType.Human,
                  content: props.query,
                },
              ],
            };
          }
        });
      });
      const extraToken = isLoginWithCognito ? getBearerTokenObj() : {};
      const param = {
        query: props.query,
        bedrock_model_id:
          props.configuration.selectedLLM || DEFAULT_QUERY_CONFIG.selectedLLM,
        use_rag_flag: true,
        visualize_results_flag: true,
        intent_ner_recognition_flag: props.configuration.intentChecked,
        agent_cot_flag: props.configuration.complexChecked,
        profile_name:
          props.configuration.selectedDataPro ||
          DEFAULT_QUERY_CONFIG.selectedDataPro,
        explain_gen_process_flag: true,
        gen_suggested_question_flag: props.configuration.modelSuggestChecked,
        answer_with_insights:
          props.configuration.answerInsightChecked ||
          DEFAULT_QUERY_CONFIG.answerInsightChecked,
        top_k: props.configuration.topK,
        top_p: props.configuration.topP,
        max_tokens: props.configuration.maxLength,
        temperature: props.configuration.temperature,
        context_window: props.configuration.contextWindow,
        session_id: props.sessionId,
        user_id: props.userId,
        //TODO remove default username
        username: props.username,
        ...extraToken,
      };
      console.log("Send WebSocketMessage: ", param);
      props.sendMessage(param);
    },
    []
  );
  return { queryWithWS };
};
