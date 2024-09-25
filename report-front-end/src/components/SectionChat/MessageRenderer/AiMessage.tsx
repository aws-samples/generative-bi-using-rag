import { Button as AmplifyBtn } from "@aws-amplify/ui-react";
import {
  Container,
  ExpandableSection,
  Flashbar,
  SpaceBetween,
  TextContent,
} from "@cloudscape-design/components";
import { SendJsonMessage } from "react-use-websocket/dist/lib/types";
import { ChatMessageProps } from ".";
import { useQueryWithTokens } from "../../../utils/api/WebSocket";
import styles from "../chat.module.scss";
import ExpandableSectionWithDivider from "../ExpandableSectionWithDivider";
import ResultRenderer from "../ResultRenderer";
import { ChatBotAnswerItem, ChatBotMessageType, QUERY_INTENT } from "../types";
import EntitySelect from "./EntitySelect";

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
                  onClick={() => {
                    queryWithWS({ query, sendJsonMessage });
                  }}
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

export type IPropsAiMessageRenderer = {
  content: ChatBotAnswerItem;
  sendJsonMessage: SendJsonMessage;
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
        <ResultRenderer
          query={content.query}
          query_intent={content.query_intent}
          result={content.sql_search_result}
          query_rewrite={content.query_rewrite}
        />
      );

    case QUERY_INTENT.reject_search:
      return <div style={{ whiteSpace: "pre-line" }}>该搜索系统暂不支持</div>;

    case QUERY_INTENT.agent_search:
      return (
        <SpaceBetween size={"m"}>
          {content.agent_search_result.agent_sql_search_result.map(
            (cnt, idx) => (
              <SpaceBetween key={idx} size={"s"}>
                <TextContent>
                  <h4>{cnt.sub_task_query}</h4>
                </TextContent>

                <ResultRenderer
                  query={cnt.sub_task_query}
                  query_intent={content.query_intent}
                  result={cnt.sql_search_result}
                  query_rewrite={content.query_rewrite}
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

export default AiMessage;
