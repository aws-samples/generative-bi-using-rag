import { Button, Container, SpaceBetween } from "@cloudscape-design/components";
import {
  Dispatch,
  SetStateAction,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import TextareaAutosize from "react-textarea-autosize";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import { v4 as uuid } from "uuid";
import { deleteHistoryBySession } from "../../utils/api/API";
import { useQueryWithTokens } from "../../utils/api/WebSocket";
import styles from "./chat.module.scss";
import CustomQuestions from "./CustomQuestions";
import { ChatBotHistoryItem, WSResponseStatusMessageItem } from "./types";

export interface ChatInputPanelProps {
  toolsHide: boolean;
  setToolsHide: Dispatch<SetStateAction<boolean>>;
  messageHistory: ChatBotHistoryItem[];
  setStatusMessage: Dispatch<SetStateAction<WSResponseStatusMessageItem[]>>;
  sendJsonMessage: SendJsonMessage;
}

export abstract class ChatScrollState {
  static userHasScrolled = false;
  static skipNextScrollEvent = false;
  static skipNextHistoryUpdate = false;
}

export default function ChatInput({
  sendJsonMessage,
  setToolsHide,
  toolsHide,
  messageHistory,
}: ChatInputPanelProps) {
  const {
    queryWithWS,
    userInfo,
    queryConfig,
    setSessions,
    currentSessionId,
    setCurrentSessionId,
    isSearching,
  } = useQueryWithTokens();

  const [query, setQuery] = useState("");

  const handleSendMessage = useCallback(() => {
    if (query === "") return;
    queryWithWS({ query, sendJsonMessage });
    setQuery("");
  }, [query, queryWithWS, sendJsonMessage]);

  useEffect(() => {
    const onWindowScroll = () => {
      if (ChatScrollState.skipNextScrollEvent) {
        ChatScrollState.skipNextScrollEvent = false;
        return;
      }

      const isScrollToTheEnd =
        Math.abs(
          window.innerHeight +
            window.scrollY -
            document.documentElement.scrollHeight
        ) <= 10;

      ChatScrollState.userHasScrolled = !isScrollToTheEnd;
    };

    window.addEventListener("scroll", onWindowScroll);

    return () => {
      window.removeEventListener("scroll", onWindowScroll);
    };
  }, []);

  useLayoutEffect(() => {
    if (ChatScrollState.skipNextHistoryUpdate) {
      ChatScrollState.skipNextHistoryUpdate = false;
      return;
    }

    if (!ChatScrollState?.userHasScrolled && messageHistory?.length > 0) {
      ChatScrollState.skipNextScrollEvent = true;
      window.scrollTo({
        top: document.documentElement.scrollHeight + 1000,
        behavior: "smooth",
      });
    }
  }, [messageHistory]);

  const refInput = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    if (!isSearching) refInput.current?.focus();
  }, [isSearching]);

  return (
    <Container className={styles.input_area_container}>
      <SpaceBetween size="s">
        <CustomQuestions sendJsonMessage={sendJsonMessage} />
        <div className={styles.input_textarea_container}>
          {/* <SpaceBetween size='xxs' direction='horizontal' alignItems='center'>
            <Icon name="microphone" variant="disabled"/>
          </SpaceBetween> */}
          <TextareaAutosize
            ref={refInput}
            className={styles.input_textarea}
            maxRows={6}
            minRows={1}
            spellCheck={true}
            autoFocus
            disabled={isSearching}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key == "Enter" && !e.shiftKey) {
                if (!e.nativeEvent.isComposing && e.locale !== "zh-CN") {
                  e.preventDefault();
                  handleSendMessage();
                }
              }
            }}
            value={query}
            placeholder={"Press ⇧ + Enter to start a new line"}
          />
          <div className={styles.input_buttons}>
            <SpaceBetween size="s" direction="horizontal">
              <Button
                loading={isSearching}
                disabled={query.length === 0 || isSearching}
                onClick={handleSendMessage}
                variant="primary"
              >
                Send
              </Button>
              <Button
                disabled={isSearching}
                iconName="remove"
                onClick={() => {
                  const bool = window.confirm(
                    "Are you sure to clear current session history?"
                  );
                  if (!bool) return;
                  const historyItem = {
                    session_id: currentSessionId,
                    user_id: userInfo.userId,
                    profile_name: queryConfig.selectedDataPro,
                  };
                  deleteHistoryBySession(historyItem).then((data) => {
                    if (!data) return;
                    setSessions((prevList) => {
                      const filteredList = prevList.filter(
                        ({ session_id }) => session_id !== currentSessionId
                      );
                      if (filteredList.length === 0) {
                        filteredList.push({
                          session_id: uuid(),
                          title: "New Chat",
                          messages: [],
                        });
                      }
                      setCurrentSessionId(filteredList[0].session_id);
                      return filteredList;
                    });
                  });
                }}
              />
              <Button
                iconName="settings"
                variant={toolsHide ? "normal" : "primary"}
                onClick={() => setToolsHide((prev) => !prev)}
              />
            </SpaceBetween>
          </div>
        </div>
      </SpaceBetween>
    </Container>
  );
}
