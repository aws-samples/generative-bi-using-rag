import { Dispatch, SetStateAction, useState } from "react";
import { ChatBotHistoryItem } from "./types";
import ChatInputPanel from "./chat-input-panel";
import styles from "./chat.module.scss";
import { Box, SpaceBetween, Spinner } from "@cloudscape-design/components";
import ChatMessage from "./chat-message";
import { BACKEND_URL } from "../../tools/const";

export default function Chat(
  props: {
    setToolsHide: Dispatch<SetStateAction<boolean>>;
  }) {

  const [messageHistory, setMessageHistory] = useState<ChatBotHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const handleFeedback = (feedbackType: "upvote" | "downvote", message: ChatBotHistoryItem) => {
    let feedbackData = {};
    if (message.query_intent === "normal_search") {
      feedbackData = {
        feedback_type: feedbackType,
        data_profiles: "shopping-demo",
        query: message.query,
        query_intent: message.query_intent,
        query_answer_list: [
          {
            query: message.query,
            sql: message.sql_search_result.sql
          }
        ]
      };
    } else if (message.query_intent === "agent_search") {
      const query_answer_list: any[] = message.agent_search_result.agent_sql_search_result.map((item: any) => {
        return {
          query: item.sub_search_task,
          sql: item.sql
        };
      });
      feedbackData = {
        feedback_type: feedbackType,
        data_profiles: "shopping-demo",
        query: message.query,
        query_intent: message.query_intent,
        query_answer_list: query_answer_list
      };
    }
    addUserFeedback(feedbackData).then();
  };

  const addUserFeedback = async (feedbackData: {}) => {
    // call api
    try {
      const url = `${BACKEND_URL}qa/user_feedback`;
      const response = await fetch(url, {
          headers: {
            "Content-Type": "application/json"
          },
          method: "POST",
          body: JSON.stringify(feedbackData)
        }
      );
      if (!response.ok) {
        console.error('AddUserFeedback error, ', response);
        return;
      }
      const result = await response.json();
    } catch (err) {
      console.error('Query error, ', err);
    }
  };

  return (
    <div className={styles.chat_container}>
      <SpaceBetween size={'l'}>
        {messageHistory.map((message, idx) => (
          <ChatMessage
            key={idx}
            message={message}
            setLoading={setLoading}
            setMessageHistory={(history: SetStateAction<ChatBotHistoryItem[]>) => setMessageHistory(history)}
            onThumbsUp={() => handleFeedback("upvote", message)}
            onThumbsDown={() => handleFeedback("downvote", message)}
          />
        ))}
        {loading && (
          <Box float="left">
            <Spinner/>
          </Box>
        )}
      </SpaceBetween>
      <div className={styles.welcome_text}>
        {messageHistory.length === 0 && !loading && (
          <center>{'GenBI Chatbot'}</center>
        )}
      </div>
      <div className={styles.input_container}>
        <ChatInputPanel
          setToolsHide={props.setToolsHide}
          setLoading={setLoading}
          messageHistory={messageHistory}
          setMessageHistory={(history: SetStateAction<ChatBotHistoryItem[]>) => setMessageHistory(history)}
        />
      </div>
    </div>
  );
}
