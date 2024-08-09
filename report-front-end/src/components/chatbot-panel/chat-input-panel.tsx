import { Button, Container, SpaceBetween } from "@cloudscape-design/components";
import {
  Dispatch,
  SetStateAction,
  useEffect,
  useLayoutEffect,
  useState,
} from "react";
import { useSelector } from "react-redux";
import TextareaAutosize from "react-textarea-autosize";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import { useQueryWithCookies } from "../../common/api/WebSocket";
import { UserState } from "../../common/helpers/types";
import {
  ChatBotHistoryItem,
  ChatBotMessageItem,
  ChatInputState,
} from "./types";
import styles from "./chat.module.scss";
import CustomQuestions from "./custom-questions";

export interface ChatInputPanelProps {
  setToolsHide: Dispatch<SetStateAction<boolean>>;
  setLoading: Dispatch<SetStateAction<boolean>>;
  messageHistory: ChatBotHistoryItem[];
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
  setStatusMessage: Dispatch<SetStateAction<ChatBotMessageItem[]>>;
  sendMessage: SendJsonMessage;
  toolsHide: boolean;
}

export abstract class ChatScrollState {
  static userHasScrolled = false;
  static skipNextScrollEvent = false;
  static skipNextHistoryUpdate = false;
}

export default function ChatInputPanel(props: ChatInputPanelProps) {
  const { queryWithWS } = useQueryWithCookies();
  const [state, setTextValue] = useState<ChatInputState>({
    value: "",
  });
  const userState = useSelector<UserState>((state) => state) as UserState;

  const handleSendMessage = () => {
    setTextValue({ value: "" });
    // Call Fast API
    /*    query({
      query: state.value,
      setLoading: props.setLoading,
      configuration: userState.queryConfig,
      setMessageHistory: props.setMessageHistory,
    }).then();*/

    if (state.value !== "") {
      // Call WebSocket API
      queryWithWS({
        query: state.value,
        configuration: userState.queryConfig,
        sendMessage: props.sendMessage,
        setMessageHistory: props.setMessageHistory,
        userId: userState.userInfo.userId,
      });
    }
  };

  const handleSetting = () => {
    props.setToolsHide((prev) => !prev);
  };

  const handleClear = () => {
    const bool = window.confirm("Are you sure to clear the chat history?");
    if (bool) props.setMessageHistory([]);
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
          sendMessage={props.sendMessage}
        />
        <div className={styles.input_textarea_container}>
          {/* <SpaceBetween size='xxs' direction='horizontal' alignItems='center'>
            <Icon name="microphone" variant="disabled"/>
          </SpaceBetween> */}
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
                // iconName='status-positive'
                variant="primary"
              >
                Send
              </Button>
              <Button iconName="remove" onClick={handleClear}></Button>
              <Button
                iconName="settings"
                variant={props.toolsHide ? "normal" : "primary"}
                onClick={handleSetting}
              ></Button>
            </SpaceBetween>
          </div>
        </div>
      </SpaceBetween>
    </Container>
  );
}
