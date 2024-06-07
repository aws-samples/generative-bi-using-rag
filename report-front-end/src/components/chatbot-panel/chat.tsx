import { Dispatch, SetStateAction, useState } from "react";
import { ChatBotHistoryItem } from "./types";
import ChatInputPanel from "./chat-input-panel";
import { Box, SpaceBetween, Spinner } from "@cloudscape-design/components";
import ChatMessage from "./chat-message";
import styles from "./chat.module.scss";

export default function Chat(
  props: {
    setToolsHide: Dispatch<SetStateAction<boolean>>;
  }) {

  const [messageHistory, setMessageHistory] = useState<ChatBotHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const scrollTo = (element : any) => {
    if (element && !isInViewPort(element)) {
      element.scrollIntoView({behavior: "smooth"});
    }
  };

  function isInViewPort(element: any) {
    const viewWidth = window.innerWidth || document.documentElement.clientWidth;
    const viewHeight = window.innerHeight || document.documentElement.clientHeight;
    const {
      top,
      right,
      bottom,
      left,
    } = element.getBoundingClientRect();

    return (
      top >= 0 && left >= 0 && right <= viewWidth && bottom <= (viewHeight - 500)
    );
  }

  return (
    <div className={styles.chat_container}>
      <SpaceBetween size={'xxl'}>
        {messageHistory.map((message, idx) => {
            const isLast = idx === messageHistory.length - 2;
            return (
              <div key={idx} ref={!loading && isLast ? scrollTo : undefined}>
                <ChatMessage
                  key={idx}
                  message={message}
                  setLoading={setLoading}
                  setMessageHistory={(history: SetStateAction<ChatBotHistoryItem[]>) => setMessageHistory(history)}
                />
              </div>
            );
          }
        )}
        {loading && (
          <div ref={loading ? scrollTo : undefined}>
            <Box float="left">
              <Spinner/>
            </Box>
          </div>
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
