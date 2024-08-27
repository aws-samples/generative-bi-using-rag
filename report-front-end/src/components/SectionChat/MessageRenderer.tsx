import { Button as AmplifyBtn } from "@aws-amplify/ui-react";
import { useCollection } from "@cloudscape-design/collection-hooks";
import {
  BarChart,
  Box,
  Button,
  ColumnLayout,
  Container,
  CopyToClipboard,
  ExpandableSection,
  Header,
  Icon,
  LineChart,
  Modal,
  Pagination,
  PieChart,
  SpaceBetween,
  Table,
  TextContent,
  TextFilter,
} from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useState } from "react";
import { useSelector } from "react-redux";
import SyntaxHighlighter from "react-syntax-highlighter";
import { SendJsonMessage } from "react-use-websocket/src/lib/types";
import { addUserFeedback } from "../../utils/api/API";
import { useQueryWithTokens } from "../../utils/api/WebSocket";
import { SQL_DISPLAY } from "../../utils/constants";
import { UserState } from "../../utils/helpers/types";
import ExpandableSectionWithDivider from "./ExpandableSectionWithDivider";
import styles from "./chat.module.scss";

import {
  ChatBotAnswerItem,
  ChatBotHistoryItem,
  ChatBotMessageType,
  FeedBackType,
  SQLSearchResult,
} from "./types";

interface ChartTypeProps {
  data_show_type: string;
  sql_data: any[][];
}

function ChartPanel(props: ChartTypeProps) {
  const sql_data = props.sql_data;
  if (props.data_show_type === "bar") {
    // convert data to bar chart data
    const header = sql_data[0];
    const items = sql_data.slice(1, sql_data.length);
    const key = ["x", "y"];
    const content = items.map((item) => {
      const map: any = new Map(
        item.map((value, index) => {
          return [key[index], value];
        })
      );
      return Object.fromEntries(map);
    });
    const seriesValue: any = [
      {
        title: header[1],
        type: "bar",
        data: content,
      },
    ];
    return (
      <BarChart
        series={seriesValue}
        height={300}
        hideFilter
        xTitle={header[0]}
        yTitle={header[1]}
      />
    );
  } else if (props.data_show_type === "line") {
    // convert data to line chart data
    const lineHeader = sql_data[0];
    const lineItems = sql_data.slice(1, sql_data.length);
    const lineKey = ["x", "y"];
    const lineContent = lineItems.map((item) => {
      const map: any = new Map(
        item.map((value, index) => {
          return [lineKey[index], value];
        })
      );
      return Object.fromEntries(map);
    });
    const lineSeriesValue: any = [
      {
        title: lineHeader[1],
        type: "line",
        data: lineContent,
      },
    ];
    return (
      <LineChart
        series={lineSeriesValue}
        height={300}
        hideFilter
        xScaleType="categorical"
        xTitle={lineHeader[0]}
        yTitle={lineHeader[1]}
      />
    );
  } else if (props.data_show_type === "pie") {
    // convert data to pie data
    const pieHeader = sql_data[0];
    const pieItems = sql_data.slice(1, sql_data.length);
    const pieKeys = ["title", "value"];
    const pieContent: any = pieItems.map((item) => {
      const map: any = new Map(
        item.map((value, index) => {
          return [pieKeys[index], value];
        })
      );
      return Object.fromEntries(map);
    });
    return (
      <PieChart
        data={pieContent}
        detailPopoverContent={(datum) => [
          { key: pieHeader[1], value: datum.value },
        ]}
        fitHeight={true}
        hideFilter
        hideLegend
      />
    );
  } else {
    return null;
  }
}

interface SQLResultProps {
  query: string;
  intent: string;
  result: SQLSearchResult;
}

/**
 * The display panel of Table, Chart, SQL etc.
 */
function SQLResultPanel(props: SQLResultProps) {
  const [selectedIcon, setSelectedIcon] = useState<FeedBackType>();
  const queryConfig = useSelector((state: UserState) => state.queryConfig);

  const sql_data = props.result?.sql_data ?? [];
  const sql_data_chart = props.result?.sql_data_chart ?? [];
  let headers: any = [];
  let content: any = [];
  if (sql_data.length > 0) {
    // convert data from server to generate table
    headers = sql_data[0].map((header: string) => {
      return {
        header: header,
        cell: (item: { [x: string]: any }) => item[header],
      };
    });
    const items = sql_data.slice(1, sql_data.length);
    content = items.map((item) => {
      const map: any = new Map(
        item.map((value, index) => {
          return [sql_data[0][index], value];
        })
      );
      return Object.fromEntries(map);
    });
  }

  const [sendingFeedback, setSendingFeedback] = useState(false);
  return (
    <div>
      <SpaceBetween size="xxl">
        {sql_data.length > 0 ? (
          <ExpandableSectionWithDivider
            variant="footer"
            defaultExpanded
            headerText="Table of Retrieved Data"
          >
            <DataTable distributions={content} header={headers} />
          </ExpandableSectionWithDivider>
        ) : null}

        {props.result.data_show_type !== "table" && sql_data.length > 0 ? (
          <ExpandableSectionWithDivider
            variant="footer"
            defaultExpanded
            headerText="Chart of Retrieved Data"
          >
            <ChartPanel
              data_show_type={props.result.data_show_type}
              sql_data={props.result.sql_data}
            />
          </ExpandableSectionWithDivider>
        ) : null}

        {props.result.data_show_type === "table" &&
        sql_data_chart.length > 0 ? (
          <ExpandableSectionWithDivider
            variant="footer"
            defaultExpanded
            headerText="Chart of Retrieved Data"
          >
            <ChartPanel
              data_show_type={sql_data_chart[0].chart_type}
              sql_data={sql_data_chart[0].chart_data}
            />
          </ExpandableSectionWithDivider>
        ) : null}

        {props.result?.data_analyse ? (
          <ExpandableSectionWithDivider
            withDivider={SQL_DISPLAY === "yes"}
            variant="footer"
            defaultExpanded
            headerText="Answer with insights"
          >
            <div style={{ whiteSpace: "pre-line" }}>
              {props.result.data_analyse}
            </div>
          </ExpandableSectionWithDivider>
        ) : null}

        {SQL_DISPLAY === "yes" && (
          <ExpandableSectionWithDivider
            withDivider={false}
            variant="footer"
            headerText="SQL & Feedbacks"
          >
            <SpaceBetween size="xl">
              <div>
                <SyntaxHighlighter language="sql" showLineNumbers wrapLines>
                  {props.result.sql}
                </SyntaxHighlighter>
                <CopyToClipboard
                  copyButtonText="Copy SQL"
                  copyErrorText="SQL failed to copy"
                  copySuccessText="SQL copied"
                  textToCopy={props.result.sql}
                />
              </div>
              <div style={{ whiteSpace: "pre-line" }}>
                {props.result.sql_gen_process}
              </div>
              <ColumnLayout columns={2}>
                {[FeedBackType.UPVOTE, FeedBackType.DOWNVOTE].map(
                  (feedback_type, index) => {
                    const isUpvote = feedback_type === FeedBackType.UPVOTE;
                    const isSelected =
                      (isUpvote && selectedIcon === FeedBackType.UPVOTE) ||
                      (!isUpvote && selectedIcon === FeedBackType.DOWNVOTE);
                    return (
                      <Button
                        key={index.toString()}
                        fullWidth
                        loading={sendingFeedback}
                        disabled={sendingFeedback}
                        variant={isSelected ? "primary" : undefined}
                        onClick={async () => {
                          setSendingFeedback(true);
                          try {
                            const res = await addUserFeedback({
                              feedback_type,
                              data_profiles: queryConfig.selectedDataPro,
                              query: props.query,
                              query_intent: props.intent,
                              query_answer: props.result.sql,
                            });
                            if (res === true) {
                              setSelectedIcon(
                                isUpvote
                                  ? FeedBackType.UPVOTE
                                  : FeedBackType.DOWNVOTE
                              );
                            } else {
                              setSelectedIcon(undefined);
                            }
                          } catch (error) {
                            console.error(error);
                          } finally {
                            setSendingFeedback(false);
                          }
                        }}
                      >
                        {isUpvote ? "👍 Upvote" : "👎 Downvote"}
                      </Button>
                    );
                  }
                )}
              </ColumnLayout>
            </SpaceBetween>
          </ExpandableSectionWithDivider>
        )}
      </SpaceBetween>
    </div>
  );
}

const DataTable = (props: { distributions: []; header: [] }) => {
  const {
    items,
    actions,
    collectionProps,
    filterProps,
    paginationProps,
    filteredItemsCount,
  } = useCollection(props.distributions, {
    pagination: { pageSize: 5 },
    sorting: {},
    filtering: {
      noMatch: (
        <Box textAlign="center" color="inherit">
          <b>No matches</b>
          <Box color="inherit" margin={{ top: "xxs", bottom: "s" }}>
            No results match your query
          </Box>
          <Button onClick={() => actions.setFiltering("")}>Clear filter</Button>
        </Box>
      ),
    },
  });

  const [visible, setVisible] = useState(false);

  return (
    <>
      <Table
        {...collectionProps}
        variant="embedded"
        columnDefinitions={props.header}
        header={
          <Header
            actions={
              <Button iconName="status-info" onClick={() => setVisible(true)}>
                Full record
              </Button>
            }
          >
            <TextContent>
              Total:{props.distributions.length} item(s)
            </TextContent>
          </Header>
        }
        items={items}
        pagination={<Pagination {...paginationProps} />}
        filter={
          <TextFilter
            {...filterProps}
            countText={`${filteredItemsCount} ${
              filteredItemsCount === 1 ? "match" : "matches"
            }`}
            filteringPlaceholder="Search"
          />
        }
        // preferences={
        //   <CollectionPreferences
        //     title="Preferences"
        //     confirmLabel="Confirm"
        //     cancelLabel="Cancel"
        //     preferences={{ pageSize: 5 }}
        //     pageSizePreference={{
        //       title: "Page size",
        //       options: [
        //         { value: 5, label: "5 resources" },
        //         { value: 10, label: "10 resources" },
        //         { value: 20, label: "20 resources" },
        //         { value: 30, label: "30 resources" },
        //       ],
        //     }}
        //   />
        // }
      />
      <Modal
        onDismiss={() => setVisible(false)}
        visible={visible}
        header={`Table - ${props.distributions.length} item(s)`}
        footer={
          <Box float="right">
            <Button variant="primary" onClick={() => setVisible(false)}>
              Close
            </Button>
          </Box>
        }
      >
        <Table
          variant="embedded"
          columnDefinitions={props.header}
          items={props.distributions}
        />
      </Modal>
    </>
  );
};

function IntentSearchPanel(props: { message: ChatBotAnswerItem }) {
  switch (props.message.query_intent) {
    case "normal_search":
      return (
        <SQLResultPanel
          query={props.message.query}
          intent={props.message.query_intent}
          result={props.message.sql_search_result}
        />
      );
    case "reject_search":
      return <div style={{ whiteSpace: "pre-line" }}>该搜索系统暂不支持</div>;
    case "agent_search":
      return (
        <SpaceBetween size={"m"}>
          {props.message.agent_search_result.agent_sql_search_result.map(
            (message, idx) => (
              <SpaceBetween key={idx} size={"s"}>
                <TextContent>
                  <h4>{message.sub_task_query}</h4>
                </TextContent>
                <SQLResultPanel
                  query={message.sub_task_query}
                  intent={props.message.query_intent}
                  result={message.sql_search_result}
                />
              </SpaceBetween>
            )
          )}
          {props.message.agent_search_result.agent_summary ? (
            <ExpandableSection
              variant="footer"
              defaultExpanded
              headerText="Answer with insights"
            >
              <div style={{ whiteSpace: "pre-line" }}>
                {props.message.agent_search_result.agent_summary}
              </div>
            </ExpandableSection>
          ) : null}
        </SpaceBetween>
      );
    case "knowledge_search":
      return (
        <div style={{ whiteSpace: "pre-line" }}>
          {props.message.knowledge_search_result.knowledge_response}
        </div>
      );
    case "ask_in_reply":
      return (
        <div style={{ whiteSpace: "pre-line" }}>
          {props.message.ask_rewrite_result.query_rewrite}
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

export interface ChatMessageProps {
  message: ChatBotHistoryItem;
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
  sendJsonMessage: SendJsonMessage;
}

export default function MessageRenderer({
  message,
  setMessageHistory,
  sendJsonMessage,
}: ChatMessageProps) {
  const { queryWithWS } = useQueryWithTokens();
  return (
    <SpaceBetween size="xs">
      {message.type === ChatBotMessageType.Human && (
        <div className={styles.question}>
          <Icon name="user-profile" /> {message.content.toString()}
        </div>
      )}
      {message.type === ChatBotMessageType.AI && (
        <Container className={styles.answer_area_container}>
          <SpaceBetween size={"s"}>
            <IntentSearchPanel message={message.content} />
            {message.content.suggested_question?.length > 0 ? (
              <ExpandableSection
                variant="footer"
                defaultExpanded
                headerText="Suggested questions"
              >
                <div className={styles.questions_grid}>
                  {message.content.suggested_question.map((query, kid) => (
                    <AmplifyBtn
                      key={kid}
                      size="small"
                      className={styles.button}
                      onClick={() =>
                        queryWithWS({
                          query,
                          sendJsonMessage,
                          setMessageHistory,
                        })
                      }
                    >
                      {query}
                    </AmplifyBtn>
                  ))}
                </div>
              </ExpandableSection>
            ) : null}
          </SpaceBetween>
        </Container>
      )}
    </SpaceBetween>
  );
}
