import { Dispatch, SetStateAction, useCallback } from "react";
import toast from "react-hot-toast";
import useWebSocket from "react-use-websocket";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import {
  ChatBotHistoryItem,
  ChatBotMessageItem,
  ChatBotMessageType,
} from "../../components/chatbot-panel/types";
import { DEFAULT_QUERY_CONFIG } from "../constant/constants";
import { Global } from "../constant/global";
import { getBearerTokenObj, getLSTokens } from "./API";

export function createWssClient(
  setStatusMessage: Dispatch<SetStateAction<ChatBotMessageItem[]>>,
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>
) {
  const socketUrl = process.env.VITE_WEBSOCKET_URL as string;
  const { sendJsonMessage } =
    // eslint-disable-next-line react-hooks/rules-of-hooks
    useWebSocket(socketUrl, {
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

  const { noToken } = getLSTokens();
  if (noToken) {
    toast.error("Please login first!");
    return;
  }

  const handleWebSocketMessage = (message: MessageEvent) => {
    console.log("Received WebSocketMessage: ", message.data);
    const messageJson = JSON.parse(message.data);
    if (messageJson.content["X-Status-Code"] === 401) {
      const patchEvent = new CustomEvent("unauthorized", {
        detail: {},
      });
      window.dispatchEvent(patchEvent);
      return;
    } else if (messageJson.content["X-Status-Code"] === 200) {
      // if (messageJson.content["X-User-Id"]) {
      //   const patchEvent = new CustomEvent("authorized", {
      //     detail: {
      //       userId: messageJson.content["X-User-Id"],
      //       userName: messageJson.content["X-User-Name"],
      //     },
      //   });
      //   window.dispatchEvent(patchEvent);
      // }
    }
    if (messageJson.content_type === "state") {
      setStatusMessage((historyMessage) => [...historyMessage, messageJson]);
    } else {
      setStatusMessage([]);
      setMessageHistory((history: ChatBotHistoryItem[]) => {
        return [
          ...history,
          {
            type: ChatBotMessageType.AI,
            content: messageJson.content,
          },
        ];
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
      userId: string;
    }) => {
      props.setMessageHistory((history: ChatBotHistoryItem[]) => {
        return [
          ...history,
          {
            type: ChatBotMessageType.Human,
            content: props.query,
          },
        ];
      });
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
        session_id: Global.sessionId,
        user_id: props.userId,
        ...getBearerTokenObj(),
      };
      console.log("Send WebSocketMessage: ", param);
      props.sendMessage(param);
    },
    []
  );
  return { queryWithWS };
};
