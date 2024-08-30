import { useCollection } from "@cloudscape-design/collection-hooks";
import {
  Box,
  Button,
  ColumnLayout,
  CopyToClipboard,
  Header,
  Modal,
  Pagination,
  SpaceBetween,
  Table,
  TextContent,
  TextFilter,
} from "@cloudscape-design/components";
import { useState } from "react";
import { useSelector } from "react-redux";
import SyntaxHighlighter from "react-syntax-highlighter";
import { addUserFeedback } from "../../utils/api/API";
import { SQL_DISPLAY } from "../../utils/constants";
import { UserState } from "../../utils/helpers/types";
import ExpandableSectionWithDivider from "./ExpandableSectionWithDivider";
import { FeedBackType, SQLSearchResult } from "./types";
import SectionChart from "./SectionChart";

interface SQLResultProps {
  query: string;
  intent: string;
  result: SQLSearchResult;
}

/**
 * The display panel of Table, Chart, SQL etc.
 */
export default function SectionSQLResult(props: SQLResultProps) {
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
            <SectionChart
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
            <SectionChart
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
