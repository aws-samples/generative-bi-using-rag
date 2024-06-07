import {
  BarChart,
  ColumnLayout,
  Container,
  ExpandableSection,
  LineChart,
  PieChart,
  SpaceBetween,
  Table,
  TextContent
} from "@cloudscape-design/components";
import {
  ChatBotAnswerItem,
  ChatBotHistoryItem,
  ChatBotMessageType, FeedBackItem, FeedBackType,
  SQLSearchResult
} from "./types";
import Button from "@cloudscape-design/components/button";
import SyntaxHighlighter from "react-syntax-highlighter";
import SuggestedQuestions from "./suggested-questions";
import { Dispatch, SetStateAction, useState } from "react";
import { addUserFeedback } from "../../common/api/API";
import { DEFAULT_QUERY_CONFIG, SQL_DISPLAY } from "../../common/constants";
import styles from "./chat.module.scss";
import { useSelector } from "react-redux";
import { UserState } from "../config-panel/types";

export interface ChartTypeProps {
  data_show_type: string;
  sql_data: any[][];
}

function ChartPanel(props: ChartTypeProps) {
  const sql_data = props.sql_data;
  if (props.data_show_type === 'bar') {// convert data to bar chart data
    const header = sql_data[0];
    const items = sql_data.slice(1, sql_data.length);
    const key = ['x', 'y'];
    const content = items.map((item) => {
      const map: any = new Map(item.map((value, index) => {
        return [key[index], value];
      }));
      return Object.fromEntries(map);
    });
    const seriesValue: any = [{
      title: header[1],
      type: "bar",
      data: content
    }];
    return (
      <BarChart
        series={seriesValue}
        height={300}
        hideFilter
        xTitle={header[0]}
        yTitle={header[1]}
      />
    );
  } else if (props.data_show_type === 'line') {// convert data to line chart data
    const lineHeader = sql_data[0];
    const lineItems = sql_data.slice(1, sql_data.length);
    const lineKey = ['x', 'y'];
    const lineContent = lineItems.map((item) => {
      const map: any = new Map(item.map((value, index) => {
        return [lineKey[index], value];
      }));
      return Object.fromEntries(map);
    });
    const lineSeriesValue: any = [{
      title: lineHeader[1],
      type: "line",
      data: lineContent
    }];
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
  } else if (props.data_show_type === 'pie') {// convert data to pie data
    const pieHeader = sql_data[0];
    const pieItems = sql_data.slice(1, sql_data.length);
    const pieKeys = ['title', 'value'];
    const pieContent: any = pieItems.map((item) => {
      const map: any = new Map(item.map((value, index) => {
        return [pieKeys[index], value];
      }));
      return Object.fromEntries(map);
    });
    return (
      <PieChart
        data={pieContent}
        detailPopoverContent={(datum) => [
          {key: pieHeader[1], value: datum.value}
        ]}
        hideFilter
      />
    );
  } else {
    return null;
  }

}

export interface SQLResultProps {
  query: string;
  intent: string;
  result: SQLSearchResult;
}

function SQLResultPanel(props: SQLResultProps) {

  const [selectedIcon, setSelectedIcon] = useState<1 | 0 | null>(null);
  const userInfo = useSelector<UserState>((state) => state) as UserState;

  const sql_data = props.result?.sql_data ?? [];
  const sql_data_chart = props.result?.sql_data_chart ?? [];
  let headers: any = [];
  let content: any = [];
  if (sql_data.length > 0) {
    // convert data from server to generate table
    headers = sql_data[0].map((header: string) => {
      return {
        header: header,
        cell: (item: { [x: string]: any; }) => item[header],
      };
    });
    const items = sql_data.slice(1, sql_data.length);
    content = items.map((item) => {
      const map: any = new Map(item.map((value, index) => {
        return [sql_data[0][index], value];
      }));
      return Object.fromEntries(map);
    });
  }
  return (
    <div>
      <SpaceBetween size={'s'}>
        {sql_data.length > 0 ?
          <ExpandableSection
            variant="footer"
            defaultExpanded
            headerText="Table">
            <Table
              columnDefinitions={headers}
              items={content}
              resizableColumns
            />
          </ExpandableSection> : null
        }
        {props.result.data_show_type !== "table" && sql_data.length > 0 ?
          <ExpandableSection
            variant="footer"
            defaultExpanded
            headerText="Chart">
            <ChartPanel
              data_show_type={props.result.data_show_type}
              sql_data={props.result.sql_data}
            />
          </ExpandableSection> : null
        }
        {props.result.data_show_type === "table" && sql_data_chart.length > 0 ?
          <ExpandableSection
            variant="footer"
            defaultExpanded
            headerText="Chart">
            <ChartPanel
              data_show_type={sql_data_chart[0].chart_type}
              sql_data={sql_data_chart[0].chart_data}
            />
          </ExpandableSection> : null
        }
        {props.result?.data_analyse ?
          <ExpandableSection
            variant="footer"
            defaultExpanded
            headerText="Answer with insights">
            <div
              style={{whiteSpace: "pre-line"}}>{props.result.data_analyse}</div>
          </ExpandableSection> : null}
        {SQL_DISPLAY === 'yes' && (
          <ExpandableSection
            variant="footer"
            headerText="SQL">
            <SpaceBetween size={'s'}>
              <div className={styles.sql}>
                <SyntaxHighlighter language="javascript">
                  {props.result.sql}
                </SyntaxHighlighter>
                <div style={{whiteSpace: "pre-line"}}>{props.result.sql_gen_process}</div>
              </div>
              <ColumnLayout columns={2}>
                <Button
                  fullWidth
                  iconName={selectedIcon === 1 ? "thumbs-up-filled" : "thumbs-up"}
                  onClick={() => {
                    const feedbackData = {
                      feedback_type: FeedBackType.UPVOTE,
                      data_profiles: userInfo.queryConfig.data_profiles || DEFAULT_QUERY_CONFIG.selectedDataPro,
                      query: props.query,
                      query_intent: props.intent,
                      query_answer: props.result.sql
                    };
                    handleFeedback(feedbackData);
                    setSelectedIcon(1);
                  }}
                >
                  Upvote
                </Button>
                <Button
                  fullWidth
                  iconName={selectedIcon === 0 ? "thumbs-down-filled" : "thumbs-down"}
                  onClick={() => {
                    const feedbackData = {
                      feedback_type: FeedBackType.DOWNVOTE,
                      data_profiles: userInfo.queryConfig.data_profiles || DEFAULT_QUERY_CONFIG.selectedDataPro,
                      query: props.query,
                      query_intent: props.intent,
                      query_answer: props.result.sql
                    };
                    handleFeedback(feedbackData);
                    setSelectedIcon(0);
                  }}
                >
                  Downvote
                </Button>
              </ColumnLayout>
            </SpaceBetween>
          </ExpandableSection>)
        }
      </SpaceBetween>
    </div>
  );
}


export interface IntentSearchProps {
  message: ChatBotAnswerItem;
}

function IntentSearchPanel(props: IntentSearchProps) {

  switch (props.message.query_intent) {
    case 'normal_search':
      return (
        <SQLResultPanel
          query={props.message.query}
          intent={props.message.query_intent}
          result={props.message.sql_search_result}
        />
      );
    case 'reject_search':
      return (
        <div style={{whiteSpace: "pre-line"}}>该搜索系统暂不支持</div>
      );
    case 'agent_search':
      return (
        <SpaceBetween size={'m'}>
          {props.message.agent_search_result.agent_sql_search_result.map((message, idx) => (
            <SpaceBetween
              key={idx}
              size={'s'}>
              <TextContent>
                <h4>{message.sub_task_query}</h4>
              </TextContent>
              <SQLResultPanel
                query={message.sub_task_query}
                intent={props.message.query_intent}
                result={message.sql_search_result}
              />
            </SpaceBetween>
          ))}
          {props.message.agent_search_result.agent_summary ?
            <ExpandableSection
              variant="footer"
              defaultExpanded
              headerText="Answer with insights">
              <div style={{whiteSpace: "pre-line"}}>{props.message.agent_search_result.agent_summary}</div>
            </ExpandableSection> : null
          }
        </SpaceBetween>
      );
    case 'knowledge_search':
      return (
        <div style={{whiteSpace: "pre-line"}}>{props.message.knowledge_search_result.knowledge_response}</div>
      );
    default:
      return (
        <div style={{whiteSpace: "pre-line"}}>结果返回错误，请检查您的网络设置，稍后请重试</div>
      );
  }
}

function AIChatMessage(props: ChatMessageProps) {

  const content = props.message.content as ChatBotAnswerItem;

  return (
    <Container>
      <SpaceBetween size={'s'}>
        <IntentSearchPanel
          message={content}
        />
        {content.suggested_question?.length > 0 ?
          <ExpandableSection
            variant="footer"
            defaultExpanded
            headerText="Suggested questions">
            <SuggestedQuestions
              questions={content.suggested_question}
              setLoading={props.setLoading}
              setMessageHistory={props.setMessageHistory}
            />
          </ExpandableSection> : null}
      </SpaceBetween>
    </Container>
  );
}

export interface ChatMessageProps {
  message: ChatBotHistoryItem;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
}

export default function ChatMessage(props: ChatMessageProps) {

  return (
    <SpaceBetween size={'m'}>
      {props.message.type === ChatBotMessageType.Human && (
        <TextContent className={styles.question}>
          <h3>{props.message.content.toString()}</h3>
        </TextContent>
      )}
      {props.message.type === ChatBotMessageType.AI && (
        <AIChatMessage
          message={props.message}
          setLoading={props.setLoading}
          setMessageHistory={props.setMessageHistory}/>
      )}
    </SpaceBetween>
  );
}

const handleFeedback = (feedbackData: FeedBackItem) => {
  addUserFeedback(feedbackData).then();
};