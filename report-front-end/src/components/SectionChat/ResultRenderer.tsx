import { useCollection } from "@cloudscape-design/collection-hooks";
import {
  Box,
  Button,
  ColumnLayout,
  CopyToClipboard,
  Form,
  FormField,
  Header,
  Modal,
  Pagination,
  Select,
  SpaceBetween,
  Table,
  Textarea,
  TextContent,
  TextFilter,
} from "@cloudscape-design/components";
import { useState } from "react";
import toast from "react-hot-toast";
import { useSelector } from "react-redux";
import SyntaxHighlighter from "react-syntax-highlighter";
import useGlobalContext from "../../hooks/useGlobalContext";
import { postUserFeedback } from "../../utils/api/API";
import { SQL_DISPLAY } from "../../utils/constants";
import { UserState } from "../../utils/helpers/types";
import ExpandableSectionWithDivider from "./ExpandableSectionWithDivider";
import ChartRenderer from "./ChartRenderer";
import { FeedBackType, SQLSearchResult } from "./types";
import { Divider } from "@aws-amplify/ui-react";

interface SQLResultProps {
  query: string;
  query_rewrite?: string;
  query_intent: string;
  result?: SQLSearchResult;
}

const OPTIONS_ERROR_CAT = (
  [
    "SQL语法错误",
    "表名错误",
    "列名错误",
    "查询值错误",
    "计算逻辑错误",
    "其他错误",
  ] as const
).map((v) => ({ value: v, label: v }));

/**
 * The display panel of Table, Chart, SQL etc.
 */
export default function ResultRenderer({
  query,
  query_rewrite,
  query_intent,
  result,
}: SQLResultProps) {
  const { currentSessionId } = useGlobalContext();
  const [selectedIcon, setSelectedIcon] = useState<FeedBackType>();
  const [sendingFeedback, setSendingFeedback] = useState(false);
  const queryConfig = useSelector((state: UserState) => state.queryConfig);
  const userInfo = useSelector((state: UserState) => state.userInfo);
  const [isDownvoteModalVisible, setIsDownvoteModalVisible] = useState(false);
  // Downvote modal hooks
  // Error description: error_description
  const [errDesc, setErrDesc] = useState("");
  // Error category: error_categories
  const [errCatOpt, setErrCatOpt] = useState(OPTIONS_ERROR_CAT[0]);
  // Correct SQL ref: correct_sql_reference
  const [correctSQL, setCorrectSQL] = useState("");
  const [isValidating, setIsValidating] = useState(false);

  if (!result) return "No SQL result in Component: <ResultRenderer />";

  const sql_data = result.sql_data ?? [];
  const sql_data_chart = result.sql_data_chart ?? [];
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

        {result.data_show_type !== "table" && sql_data.length > 0 ? (
          <ExpandableSectionWithDivider
            variant="footer"
            defaultExpanded
            headerText="Chart of Retrieved Data"
          >
            <ChartRenderer
              data_show_type={result.data_show_type}
              sql_data={result.sql_data}
            />
          </ExpandableSectionWithDivider>
        ) : null}

        {result.data_show_type === "table" && sql_data_chart.length > 0 ? (
          <ExpandableSectionWithDivider
            variant="footer"
            defaultExpanded
            headerText="Chart of Retrieved Data"
          >
            <ChartRenderer
              data_show_type={sql_data_chart[0].chart_type}
              sql_data={sql_data_chart[0].chart_data}
            />
          </ExpandableSectionWithDivider>
        ) : null}

        {result?.data_analyse ? (
          <ExpandableSectionWithDivider
            withDivider={SQL_DISPLAY === "yes"}
            variant="footer"
            defaultExpanded
            headerText="Answer with insights"
          >
            <div style={{ whiteSpace: "pre-line" }}>{result.data_analyse}</div>
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
                  {result.sql}
                </SyntaxHighlighter>
                <CopyToClipboard
                  copyButtonText="Copy SQL"
                  copyErrorText="SQL failed to copy"
                  copySuccessText="SQL copied"
                  textToCopy={result.sql}
                />
              </div>
              <div style={{ whiteSpace: "pre-line" }}>
                {result.sql_gen_process}
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
                          if (isUpvote) {
                            setSendingFeedback(true);
                            try {
                              const res = await postUserFeedback({
                                feedback_type,
                                data_profiles: queryConfig.selectedDataPro,
                                query: query_rewrite || query,
                                query_intent,
                                query_answer: result.sql,
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
                          } else {
                            // is downvoting
                            setIsDownvoteModalVisible(true);
                          }
                        }}
                      >
                        {isUpvote ? "👍 Upvote" : "👎 Downvote"}
                      </Button>
                    );
                  }
                )}
              </ColumnLayout>

              <Modal
                onDismiss={() => {
                  setIsDownvoteModalVisible(false);
                  setIsValidating(false);
                }}
                visible={isDownvoteModalVisible}
                header="Downvote Questionnaire"
                footer={
                  <Box float="right">
                    <Button
                      variant="primary"
                      onClick={async () => {
                        setIsValidating(true);
                        if (!errDesc)
                          return toast.error(
                            "Please provide the missing information in the form before submission..."
                          );
                        setSendingFeedback(true);
                        try {
                          const res = await postUserFeedback({
                            feedback_type: FeedBackType.DOWNVOTE,
                            data_profiles: queryConfig.selectedDataPro,
                            query: query_rewrite || query,
                            query_intent: query_intent,
                            query_answer: result.sql,
                            session_id: currentSessionId,
                            user_id: userInfo.userId,
                            error_description: errDesc,
                            error_categories: errCatOpt.value,
                            correct_sql_reference: correctSQL,
                          });
                          if (res === true) {
                            setSelectedIcon(FeedBackType.DOWNVOTE);
                            toast.success("Thanks for your feedback!");
                            // resetting form
                            setIsValidating(false);
                            setErrCatOpt(OPTIONS_ERROR_CAT[0]);
                            setErrDesc("");
                            setCorrectSQL("");
                          }
                        } catch (error) {
                          console.error("Error on sending feedback...", error);
                          toast.error("Error on sending feedback...");
                        } finally {
                          setSendingFeedback(false);
                        }
                      }}
                    >
                      Submit
                    </Button>
                  </Box>
                }
              >
                <Box padding={{ top: "l", bottom: "m" }}>
                  <Divider label="Existing Information" />
                </Box>
                <form onSubmit={(e) => e.preventDefault()}>
                  <Form>
                    <SpaceBetween size="l">
                      <FormField label="Query">{query_rewrite}</FormField>
                      <FormField label="Answer">
                        <SyntaxHighlighter
                          language="sql"
                          showLineNumbers
                          wrapLines
                        >
                          {result.sql.replace(/^\n/, "").replace(/\n$/, "")}
                        </SyntaxHighlighter>
                      </FormField>

                      <Divider label="Feedback Form" />
                      <FormField label="Error category *">
                        <Select
                          options={OPTIONS_ERROR_CAT}
                          selectedOption={errCatOpt}
                          onChange={({ detail }) =>
                            // options are fixed values, no need for type checking
                            setErrCatOpt(detail.selectedOption as any)
                          }
                        />
                      </FormField>
                      <FormField
                        label="Error description *"
                        warningText={
                          isValidating &&
                          !errDesc &&
                          "This field can NOT be empty"
                        }
                      >
                        <Textarea
                          placeholder="Please provide a brief description of the error occurred"
                          value={errDesc}
                          onChange={({ detail }) => setErrDesc(detail.value)}
                        />
                      </FormField>
                      <FormField label="Correct SQL ref">
                        <Textarea
                          onChange={({ detail }) => setCorrectSQL(detail.value)}
                          value={correctSQL}
                          placeholder="Please provide a correct SQL for reference"
                        />
                      </FormField>
                    </SpaceBetween>
                  </Form>
                </form>
              </Modal>
            </SpaceBetween>
          </ExpandableSectionWithDivider>
        )}
      </SpaceBetween>
    </div>
  );
}
const DataTable = ({
  distributions,
  header,
}: {
  distributions: [];
  header: [];
}) => {
  const {
    items,
    actions,
    collectionProps,
    filterProps,
    paginationProps,
    filteredItemsCount,
  } = useCollection(distributions, {
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
        columnDefinitions={header}
        header={
          <Header
            actions={
              <Button iconName="status-info" onClick={() => setVisible(true)}>
                Full record
              </Button>
            }
          >
            <TextContent>Total:{distributions.length} item(s)</TextContent>
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
        header={`Table - ${distributions.length} item(s)`}
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
          columnDefinitions={header}
          items={distributions}
        />
      </Modal>
    </>
  );
};
