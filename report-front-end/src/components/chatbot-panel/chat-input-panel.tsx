import { Button, Container, Icon, SpaceBetween, } from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useLayoutEffect, useState, } from "react";
import TextareaAutosize from "react-textarea-autosize";
import { ChatBotHistoryItem, ChatBotMessageItem, ChatInputState, } from "./types";
import CustomQuestions from "./custom-questions";
import { useSelector } from "react-redux";
import { UserState } from "../config-panel/types";
import styles from "./chat.module.scss";
import { queryWithWS } from "../../common/api/WebSocket";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";

export interface ChatInputPanelProps {
  setToolsHide: Dispatch<SetStateAction<boolean>>;
  setLoading: Dispatch<SetStateAction<boolean>>;
  messageHistory: ChatBotHistoryItem[];
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
  setStatusMessage: Dispatch<SetStateAction<ChatBotMessageItem[]>>;
  sendMessage: SendJsonMessage;
}

export abstract class ChatScrollState {
  static userHasScrolled = false;
  static skipNextScrollEvent = false;
  static skipNextHistoryUpdate = false;
}

export default function ChatInputPanel(props: ChatInputPanelProps) {
  const [state, setTextValue] = useState<ChatInputState>({
    value: ""
  });
  const userInfo = useSelector<UserState>((state) => state) as UserState;

  const handleSendMessage = () => {
    setTextValue({value: ""});
    // Call Fast API
/*    query({
      query: state.value,
      setLoading: props.setLoading,
      configuration: userInfo.queryConfig,
      setMessageHistory: props.setMessageHistory,
    }).then();*/

    // Call WebSocket API
    queryWithWS({
      query: state.value,
      configuration: userInfo.queryConfig,
      sendMessage: props.sendMessage,
      setMessageHistory: props.setMessageHistory
    });
  };

  const handleSetting = () => {
    props.setToolsHide(false);
  };

  const handleClear = () => {
    props.setMessageHistory([]);
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
      <SpaceBetween size={'s'}>
        <CustomQuestions
          setTextValue={setTextValue}
          setLoading={props.setLoading}
          setMessageHistory={props.setMessageHistory}
          sendMessage={props.sendMessage}
        ></CustomQuestions>
        <div className={styles.input_textarea_container}>
          <SpaceBetween size="xxs" direction="horizontal" alignItems="center">
            <Icon name="microphone" variant="disabled"/>
          </SpaceBetween>
          <TextareaAutosize
            className={styles.input_textarea}
            maxRows={6}
            minRows={1}
            spellCheck={true}
            autoFocus
            onChange={(e) =>
              setTextValue((state) => ({...state, value: e.target.value}))
            }
            value={state.value}
            placeholder={"Send a message"}
          />
          <SpaceBetween size={'xs'} direction={'horizontal'}>
            <Button
              disabled={state.value.length === 0}
              onClick={handleSendMessage}
              iconAlign="left"
              iconName="status-positive"
              variant="primary">
              Send
            </Button>
            <Button
              iconName="remove"
              variant="icon"
              onClick={handleClear}
            >
            </Button>
            <Button
              iconName="settings"
              variant="icon"
              onClick={handleSetting}>
            </Button>
          </SpaceBetween>
        </div>
      </SpaceBetween>
    </Container>
  );
}
