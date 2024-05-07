import {
  BarChart,
  Box,
  Container,
  ExpandableSection,
  SpaceBetween,
  Table,
  TextContent
} from "@cloudscape-design/components";
import { ChatBotHistoryItem } from "./types";
import Button from "@cloudscape-design/components/button";
import SyntaxHighlighter from "react-syntax-highlighter";
import styles from "../../styles/chat.module.scss";

export interface ChatMessageProps {
  message: ChatBotHistoryItem;
  onThumbsUp: () => void;
  onThumbsDown: () => void;
}

export default function ChatMessage(props: ChatMessageProps) {

  switch (props.message.query_intent) {
    case 'normal_search':
      const sql_data = props.message.sql_search_result.sql_data;
      /* for (let i = 0; i < sql_data.length; i++) {
           console.log(sql_data[i]);
           if (i === 0) {
               const header = [];
               for (let j = 0; j < sql_data[0].length; j++) {
                   header[j] = {
                       header: sql_data[0][j],
                       cell: (e: { name: any; }) => e.name
                   };
               }
               console.log(header);
           }
       }*/
      return (
        <SpaceBetween size={'m'}>
          <TextContent>
            <strong>{props.message.query}</strong>
          </TextContent>
          <Container>
            <SpaceBetween size={'s'}>
              {props.message.sql_search_result.data_show_type === "table" ?
                <ExpandableSection
                  variant="footer"
                  defaultExpanded
                  headerText="Table">
                  <Table
                    columnDefinitions={[
                      {
                        header: "Variable name",
                        cell: e => e.name
                      },
                      {
                        header: "Type",
                        cell: e => e.type
                      },
                      {
                        header: "Size",
                        cell: e => e.size
                      }
                    ]}
                    enableKeyboardNavigation
                    items={[
                      {
                        name: "Item 1",
                        type: "1A",
                        size: "Small"
                      },
                      {
                        name: "Item 2",
                        type: "1B",
                        size: "Large"
                      },
                      {
                        name: "Item 3",
                        type: "1A",
                        size: "Large"
                      }
                    ]}
                    resizableColumns
                    empty={
                      <Box
                        margin={{vertical: "xs"}}
                        textAlign="center"
                        color="inherit"
                      >
                        <SpaceBetween size="m">
                          <b>No resources</b>
                          <Button>Create resource</Button>
                        </SpaceBetween>
                      </Box>
                    }
                  />
                </ExpandableSection> : null}
              <ExpandableSection
                variant="footer"
                defaultExpanded
                headerActions={<Button>Edit</Button>}
                headerText="Chart">
                <BarChart
                  series={[
                    {
                      title: "Sale count",
                      type: "bar",
                      data: [
                        {x: "0790267c", y: 65},
                        {x: "575c0ac0", y: 48},
                        {x: "b20ba076", y: 46},
                        {x: "aff05423", y: 44},
                        {x: "0987bfa1", y: 42}
                      ]
                    }
                  ]}
                  ariaLabel="Single data series line chart"
                  height={300}
                  hideFilter
                />
              </ExpandableSection>
              <ExpandableSection
                variant="footer"
                defaultExpanded
                headerText="Answer with insights">
                <div
                  style={{whiteSpace: "pre-line"}}>{props.message.sql_search_result.data_analyse}</div>
              </ExpandableSection>
              <ExpandableSection
                variant="footer"
                headerText="SQL">
                <div className={styles.sql}>
                  <SyntaxHighlighter language="javascript">
                    {props.message.sql_search_result.sql}
                  </SyntaxHighlighter>
                  <div
                    style={{whiteSpace: "pre-line"}}>{props.message.sql_search_result.sql_gen_process}</div>
                </div>
              </ExpandableSection>
            </SpaceBetween>
          </Container>
        </SpaceBetween>
      );
    case 'reject_search':
      return <></>;
    case 'agent_search':
      return <></>;
    case 'knowledge_search':
      return <></>;
    default:
      return <></>;
  }
}