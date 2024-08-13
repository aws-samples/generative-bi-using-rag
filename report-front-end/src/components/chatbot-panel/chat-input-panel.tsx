import { Button, Container, SpaceBetween } from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useLayoutEffect, useState } from "react";
import { useSelector } from "react-redux";
import TextareaAutosize from "react-textarea-autosize";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import { queryWithWS } from "../../common/api/WebSocket";
import { UserState } from "../../common/helpers/types";
import { ChatBotHistoryItem, ChatBotMessageItem, ChatInputState } from "./types";
import styles from "./chat.module.scss";
import CustomQuestions from "./custom-questions";
import { Session } from "../session-panel/types";
import { deleteHistoryBySession } from "../../common/api/API";
import { v4 as uuid } from "uuid";

export interface ChatInputPanelProps {
  setToolsHide: Dispatch<SetStateAction<boolean>>;
  setLoading: Dispatch<SetStateAction<boolean>>;
  messageHistory: ChatBotHistoryItem[];
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
  sessions: Session[];
  setSessions: Dispatch<SetStateAction<Session[]>>;
  setStatusMessage: Dispatch<SetStateAction<ChatBotMessageItem[]>>;
  sendMessage: SendJsonMessage;
  toolsHide: boolean;
  currSessionId: string;
  setCurrentSessionId: Dispatch<SetStateAction<string>>;
}

export abstract class ChatScrollState {
  static userHasScrolled = false;
  static skipNextScrollEvent = false;
  static skipNextHistoryUpdate = false;
}

export default function ChatInputPanel(props: ChatInputPanelProps) {
  const [state, setTextValue] = useState<ChatInputState>({
    value: "",
  });
  const userState = useSelector<UserState>((state) => state) as UserState;

  const handleSendMessage = () => {
    setTextValue({ value: "" });
    if (state.value !== "") {
      // Call WebSocket API
      queryWithWS({
        query: state.value,
        configuration: userState.queryConfig,
        sendMessage: props.sendMessage,
        setSessions: props.setSessions,
        setMessageHistory: props.setMessageHistory,
        userId: userState.userInfo.userId,
        sessionId: props.currSessionId,
      });
    }
  };

  const handleSetting = () => {
    props.setToolsHide((prev) => !prev);
  };

  const handleClear = () => {
    const bool = window.confirm("Are you sure to clear current session history?");
    // if (bool) props.setMessageHistory([]);
    if (bool) {
      const historyItem = {
        session_id: props.currSessionId,
        user_id: userState.userInfo.userId,
        profile_name: userState.queryConfig.selectedDataPro,
      };
      deleteHistoryBySession(historyItem).then(
        response => {
          if (response) {
            props.setSessions((prevState: Session[]) => {
              const filterState = prevState.filter((item: Session) => {
                return item.session_id !== props.currSessionId;
              });
              if (filterState.length === 0) {
                filterState.push({
                  session_id: uuid(),
                  title: "New Chat",
                  messages: [],
                });
              }
              props.setCurrentSessionId(filterState[0].session_id);
              return filterState;
            });
          }
        },
      );
    }
  };

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
          document.documentElement.scrollHeight,
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

    if (!ChatScrollState.userHasScrolled && props.messageHistory.length > 0) {
      ChatScrollState.skipNextScrollEvent = true;
      window.scrollTo({
        top: document.documentElement.scrollHeight + 1000,
        behavior: "smooth",
      });
    }
  }, [props.messageHistory]);

  return (
    <Container className={styles.input_area_container}>
      <SpaceBetween size="s">
        <CustomQuestions
          setTextValue={setTextValue}
          setLoading={props.setLoading}
          setMessageHistory={props.setMessageHistory}
          setSessions={props.setSessions}
          sendMessage={props.sendMessage}
          sessionId={props.currSessionId}
        />
        <div className={styles.input_textarea_container}>
          <TextareaAutosize
            className={styles.input_textarea}
            maxRows={6}
            minRows={1}
            spellCheck={true}
            autoFocus
            onChange={(e) =>
              setTextValue((state) => ({ ...state, value: e.target.value }))
            }
            onKeyDown={(e) => {
              if (e.key == "Enter" && !e.shiftKey) {
                if (!e.nativeEvent.isComposing && e.locale !== "zh-CN") {
                  e.preventDefault();
                  handleSendMessage();
                }
              }
            }}
            value={state.value}
            placeholder={"Press ⇧ + Enter to start a new line"}
          />
          <div className={styles.input_buttons}>
            <SpaceBetween size="s" direction="horizontal">
              <Button
                disabled={state.value.length === 0}
                onClick={handleSendMessage}
                variant="primary"
              >
                Send
              </Button>
              <Button iconName="remove" onClick={handleClear}></Button>
              <Button
                iconName="settings"
                variant={props.toolsHide ? "normal" : "primary"}
                onClick={handleSetting}
              />
            </SpaceBetween>
          </div>
        </div>
      </SpaceBetween>
    </Container>
  );
}
