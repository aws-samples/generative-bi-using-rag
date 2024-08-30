import { Button as AmplifyBtn } from "@aws-amplify/ui-react";
import {
  Box,
  Button,
  Container,
  ExpandableSection,
  Flashbar,
  Icon,
  RadioGroup,
  SpaceBetween,
  TextContent,
} from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import { useQueryWithTokens } from "../../utils/api/WebSocket";
import ExpandableSectionWithDivider from "./ExpandableSectionWithDivider";
import SectionSQLResult from "./SectionSQLResult";
import styles from "./chat.module.scss";
import {
  ChatBotAnswerItem,
  ChatBotHistoryItem,
  ChatBotMessageType,
  IEntityItem,
  QUERY_INTENT,
} from "./types";

interface ChatMessageProps<T = ChatBotHistoryItem> {
  message: T;
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
  sendJsonMessage: SendJsonMessage;
}

export default function MessageRenderer({
  message,
  sendJsonMessage,
}: ChatMessageProps) {
  return (
    <SpaceBetween size="xs">
      {message.type === ChatBotMessageType.Human && (
        <div className={styles.question}>
          <Icon name="user-profile" /> {message.content.toString()}
        </div>
      )}
      {message.type === ChatBotMessageType.AI && (
        <AiMessage {...{ message, sendJsonMessage }} />
      )}
    </SpaceBetween>
  );
}

const AiMessage: React.FC<
  Omit<
    ChatMessageProps<{
      type: ChatBotMessageType.AI;
      content: ChatBotAnswerItem;
    }>,
    "setMessageHistory"
  >
> = ({ message, sendJsonMessage }) => {
  const { queryWithWS } = useQueryWithTokens();
  if (!message?.content) return <>No message.content</>;
  const { content } = message;

  return (
    <Container className={styles.answer_area_container}>
      <SpaceBetween size="s">
        {!Object.entries(content.error_log).length ? null : (
          <ExpandableSectionWithDivider
            variant="footer"
            defaultExpanded
            headerText="Error Log"
          >
            <SpaceBetween size="s">
              {Object.entries(content.error_log).map(([k, v], idx) => (
                <Flashbar
                  key={idx}
                  items={[
                    {
                      type: "warning",
                      dismissible: false,
                      content: `[ ${k} ] ${v}`,
                      id: k,
                    },
                  ]}
                />
              ))}
            </SpaceBetween>
          </ExpandableSectionWithDivider>
        )}

        <AiMessageRenderer
          content={content}
          sendJsonMessage={sendJsonMessage}
        />

        {content.suggested_question?.length > 0 ? (
          <ExpandableSection
            variant="footer"
            defaultExpanded
            headerText="Suggested questions"
          >
            <div className={styles.questions_grid}>
              {content.suggested_question.map((query, kid) => (
                <AmplifyBtn
                  key={kid}
                  size="small"
                  className={styles.button}
                  onClick={() => queryWithWS({ query, sendJsonMessage })}
                >
                  {query}
                </AmplifyBtn>
              ))}
            </div>
          </ExpandableSection>
        ) : null}
      </SpaceBetween>
    </Container>
  );
};

function AiMessageRenderer({
  content,
  sendJsonMessage,
}: IPropsAiMessageRenderer) {
  switch (content.query_intent) {
    case QUERY_INTENT.entity_select:
      return <EntitySelect {...{ content, sendJsonMessage }} />;

    case QUERY_INTENT.normal_search:
      return (
        <SectionSQLResult
          query={content.query}
          intent={content.query_intent}
          result={content.sql_search_result}
        />
      );

    case QUERY_INTENT.reject_search:
      return <div style={{ whiteSpace: "pre-line" }}>该搜索系统暂不支持</div>;

    case QUERY_INTENT.agent_search:
      return (
        <SpaceBetween size={"m"}>
          {content.agent_search_result.agent_sql_search_result.map(
            (content, idx) => (
              <SpaceBetween key={idx} size={"s"}>
                <TextContent>
                  <h4>{content.sub_task_query}</h4>
                </TextContent>

                <SectionSQLResult
                  query={content.sub_task_query}
                  intent={content.query_intent}
                  result={content.sql_search_result}
                />
              </SpaceBetween>
            )
          )}

          {content.agent_search_result.agent_summary ? (
            <ExpandableSection
              variant="footer"
              defaultExpanded
              headerText="Answer with insights"
            >
              <div style={{ whiteSpace: "pre-line" }}>
                {content.agent_search_result.agent_summary}
              </div>
            </ExpandableSection>
          ) : null}
        </SpaceBetween>
      );

    case QUERY_INTENT.knowledge_search:
      return (
        <div style={{ whiteSpace: "pre-line" }}>
          {content.knowledge_search_result.knowledge_response}
        </div>
      );

    case QUERY_INTENT.ask_in_reply:
      return (
        <div style={{ whiteSpace: "pre-line" }}>
          {content.ask_rewrite_result.query_rewrite}
        </div>
      );

    default:
      return (
        <div style={{ whiteSpace: "pre-line" }}>
          结果返回错误，请检查您的网络设置，稍后请重试
        </div>
      );
  }
}

type IPropsAiMessageRenderer = {
  content: ChatBotAnswerItem;
  sendJsonMessage: SendJsonMessage;
};

function EntitySelect({ content, sendJsonMessage }: IPropsAiMessageRenderer) {
  const entities = content.ask_entity_select?.entity_select_info;

  const { queryWithWS } = useQueryWithTokens();
  const [userSelected, setUserSelected] = useState<
    Record<string, Record<string, string>>
  >({});
  const [selectedIdRecord, setSelectedIdRecord] = useState<
    Record<string, string>
  >({});
  useEffect(() => {
    if (!entities) return;
    Object.entries(selectedIdRecord).forEach(([tp, selectedId]) => {
      const arr = entities[tp];
      setUserSelected((prev) => ({
        ...prev,
        [tp]: arr.find(({ id }) => id === selectedId)!,
      }));
    });
  }, [entities, selectedIdRecord]);

  if (!entities) return null;
  return (
    <Box>
      <SpaceBetween size="l">
        <Box margin={{ bottom: "s" }}>
          Please select the correct entity you would like to query -
        </Box>
        {Object.entries(entities).map(([type, vObj], idx) => {
          return (
            <EntityRadioSelect
              key={idx}
              type={type}
              vObj={vObj}
              setSelectedIdRecord={setSelectedIdRecord}
            />
          );
        })}
        <Box margin={{ top: "xxl" }}>
          <Button
            variant="primary"
            disabled={Object.keys(selectedIdRecord).length === 0}
            iconName="status-positive"
            onClick={() => {
              queryWithWS({
                query: content.query,
                sendJsonMessage: sendJsonMessage,
                extraParams: {
                  query_rewrite: content.query_rewrite,
                  previous_intent: QUERY_INTENT.entity_select,
                  entity_user_select: userSelected,
                  entity_retrieval: content.ask_entity_select.entity_retrieval,
                },
              });
              setUserSelected({});
              setSelectedIdRecord({});
            }}
          >
            Continue...
          </Button>
        </Box>
      </SpaceBetween>
    </Box>
  );
}

function EntityRadioSelect({
  type,
  vObj,
  setSelectedIdRecord,
}: {
  type: string;
  vObj: Array<IEntityItem>;
  setSelectedIdRecord: Dispatch<SetStateAction<Record<string, string>>>;
}) {
  const [id, setId] = useState("");

  return (
    <Box>
      <Box variant="h3">{type}</Box>
      <RadioGroup
        onChange={({ detail }) => {
          setId(detail.value);
          setSelectedIdRecord((prev) => {
            return { ...prev, [type]: detail.value };
          });
        }}
        value={id}
        items={vObj.map(({ text, id }) => ({
          value: id,
          label: text,
        }))}
      />
    </Box>
  );
}
