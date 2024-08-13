import useWebSocket from "react-use-websocket";
import { DEFAULT_QUERY_CONFIG } from "../constant/constants";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import { Dispatch, SetStateAction } from "react";
import { ChatBotMessageItem, ChatBotMessageType } from "../../components/chatbot-panel/types";
import { Session } from "../../components/session-panel/types";

export function createWssClient(
  setStatusMessage: Dispatch<SetStateAction<ChatBotMessageItem[]>>,
  setSessions: Dispatch<SetStateAction<Session[]>>
) {
  const socketUrl = process.env.VITE_WEBSOCKET_URL as string;
  const {sendJsonMessage}
    // eslint-disable-next-line react-hooks/rules-of-hooks
    = useWebSocket(socketUrl, {
    onOpen: (openMessage) => console.log('websocket connection opened, ', openMessage),
    onClose: (closeMessage) => console.error('websocket connection closed, ', closeMessage),
    onError: (errorMessage) => console.error('websocket connection error, ', errorMessage),
    //Will attempt to reconnect on all close events, such as server shutting down
    shouldReconnect: () => true,
    onMessage: (message) => handleWebSocketMessage(message)
  });

  const handleWebSocketMessage = (message: MessageEvent) => {
    console.log("Received WebSocketMessage: ", message.data);
    const messageJson = JSON.parse(message.data);
    if (messageJson.content_type === "state") {
      setStatusMessage((historyMessage) =>
        [...historyMessage, messageJson]);
    } else {
      setStatusMessage([]);
      setSessions((prevState) => {
        return prevState.map((session) => {
          if (messageJson.session_id !== session.session_id) {
            return session;
          } else {
            return {
              session_id: messageJson.session_id,
              messages: [...session.messages, {
                type: ChatBotMessageType.AI,
                content: messageJson.content
              }]
            }
          }
        })
      });

    }
  };

  return sendJsonMessage;
}

export function queryWithWS(props: {
  query: string;
  configuration: any;
  sendMessage: SendJsonMessage;
  setSessions: Dispatch<SetStateAction<Session[]>>;
  userId: string;
  sessionId: string;
}) {
  props.setSessions((prevState) => {
    return prevState.map((session) => {
      if (props.sessionId !== session.session_id) {
        return session;
      } else {
        return {
          session_id: session.session_id,
          messages: [...session.messages, {
            type: ChatBotMessageType.Human,
            content: props.query
          }]
        }
      }
    })
  });
  const param = {
    query: props.query,
    bedrock_model_id: props.configuration.selectedLLM || DEFAULT_QUERY_CONFIG.selectedLLM,
    use_rag_flag: true,
    visualize_results_flag: true,
    intent_ner_recognition_flag: props.configuration.intentChecked,
    agent_cot_flag: props.configuration.complexChecked,
    profile_name: props.configuration.selectedDataPro || DEFAULT_QUERY_CONFIG.selectedDataPro,
    explain_gen_process_flag: true,
    gen_suggested_question_flag: props.configuration.modelSuggestChecked,
    answer_with_insights: props.configuration.answerInsightChecked || DEFAULT_QUERY_CONFIG.answerInsightChecked,
    top_k: props.configuration.topK,
    top_p: props.configuration.topP,
    max_tokens: props.configuration.maxLength,
    temperature: props.configuration.temperature,
    context_window: props.configuration.contextWindow,
    session_id: props.sessionId,
    user_id: props.userId
  };
  console.log("Send WebSocketMessage: ", param);
  props.sendMessage(param);
}
