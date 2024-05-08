import { Button, Container, Icon, SpaceBetween, } from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useLayoutEffect, useState, } from "react";
import TextareaAutosize from "react-textarea-autosize";
import styles from "../../styles/chat.module.scss";
import { ChatBotConfiguration, ChatBotHistoryItem, ChatInputState, } from "./types";
import CustomQuestions from "./custom-questions";
import data from "../../mockdata/answers_line.json";

export interface ChatInputPanelProps {
  running: boolean;
  setRunning: Dispatch<SetStateAction<boolean>>;
  configuration: ChatBotConfiguration;
  setConfiguration: Dispatch<SetStateAction<ChatBotConfiguration>>;
  messageHistory: ChatBotHistoryItem[];
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>,
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

  function query() {
    const url = "";
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
      .then(res => {
        if (!res.ok) {
          throw new Error('Network response was not ok');
        }
        return res;
      })
      .then(data => {
        // todo: setQueryAnswers
      })
      .catch(err => {
        console.error(err);
        return err;
      });
  }

  const handleSendMessage = () => {
    setTextValue({value: ""});
    // query();

    const answers = data;
    console.log(answers);
    props.setMessageHistory((history: ChatBotHistoryItem[]) => {
      console.log([...history, data]);
      return [...history, data];
    });
  };

  return (
    <SpaceBetween direction="vertical" size="l">
      <div className={styles.input_area_container}>
        <Container>
          <SpaceBetween size={'s'}>
            <CustomQuestions setTextValue={setTextValue}></CustomQuestions>
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
                onKeyDown={(e) => {
                  if (e.key == "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                value={state.value}
                placeholder={"Send a message"}
              />
              <div style={{marginLeft: "8px"}}>
                <Button
                  disabled={state.value.length === 0}
                  onClick={handleSendMessage}
                  iconAlign="right"
                  iconName={!props.running ? "angle-right-double" : undefined}
                  variant="primary">
                  Send
                </Button>
                <Button
                  iconName="settings"
                  variant="icon"
                />
              </div>
            </div>
          </SpaceBetween>
        </Container>
        {/*<StatusIndicator type={"success"}>
                    {"Connected"}
                </StatusIndicator>*/}
      </div>
    </SpaceBetween>
  );
}
