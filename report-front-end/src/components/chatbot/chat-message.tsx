import {
    BarChart,
    Box,
    Container,
    ExpandableSection,
    SpaceBetween,
    Table,
    TextContent
} from "@cloudscape-design/components";
import { ChatBotHistoryItem, ChatBotMessageType } from "./types";
import Button from "@cloudscape-design/components/button";
import SyntaxHighlighter from "react-syntax-highlighter";
import styles from "../../styles/chat.module.scss";
import { data_analyse, sql, sql_gen_process } from "../../mockdata/constant";

export interface ChatMessageProps {
    message: ChatBotHistoryItem;
    onThumbsUp: () => void;
    onThumbsDown: () => void;
}

export default function ChatMessage(props: ChatMessageProps) {

    return (
        <SpaceBetween size={'m'}>
            {/*{props.message?.type === ChatBotMessageType.AI && (
                <Container>
                    <TextContent>
                        <strong>{props.message.content}</strong>
                    </TextContent>
                </Container>
            )}*/}
            {props.message?.type === ChatBotMessageType.Human && (
                <TextContent>
                    <strong>{props.message.content}</strong>
                </TextContent>
            )}
            <Container>
                <SpaceBetween size={'s'}>
                    <ExpandableSection
                        variant="footer"
                        defaultExpanded
                        headerText="Table">
                        <Table
                            columnDefinitions={[
                                {
                                    id: "variable",
                                    header: "Variable name",
                                    cell: e => e.name,
                                    width: 170,
                                    minWidth: 165,
                                    sortingField: "name",
                                    isRowHeader: true
                                },
                                {
                                    id: "type",
                                    header: "Type",
                                    cell: e => e.type,
                                    width: 110,
                                    minWidth: 110,
                                    sortingField: "type"
                                },
                                {
                                    id: "size",
                                    header: "Size",
                                    cell: e => e.size,
                                    width: 110,
                                    minWidth: 90
                                },
                                {
                                    id: "description",
                                    header: "Description",
                                    cell: e => e.description,
                                    width: 200,
                                    minWidth: 170
                                }
                            ]}
                            enableKeyboardNavigation
                            items={[
                                {
                                    name: "Item 1",
                                    alt: "First",
                                    description: "This is the first item",
                                    type: "1A",
                                    size: "Small"
                                },
                                {
                                    name: "Item 2",
                                    alt: "Second",
                                    description: "This is the second item",
                                    type: "1B",
                                    size: "Large"
                                },
                                {
                                    name: "Item 3",
                                    alt: "Third",
                                    description: "-",
                                    type: "1A",
                                    size: "Large"
                                },
                                {
                                    name: "Item 4",
                                    alt: "Fourth",
                                    description: "This is the fourth item",
                                    type: "2A",
                                    size: "Small"
                                },
                                {
                                    name: "Item 5",
                                    alt: "-",
                                    description:
                                        "This is the fifth item with a longer description",
                                    type: "2A",
                                    size: "Large"
                                },
                                {
                                    name: "Item 6",
                                    alt: "Sixth",
                                    description: "This is the sixth item",
                                    type: "1A",
                                    size: "Small"
                                }
                            ]}
                            resizableColumns
                            selectedItems={[{ name: "Item 2" }]}
                            empty={
                                <Box
                                    margin={{ vertical: "xs" }}
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
                    </ExpandableSection>
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
                                        { x: "0790267c", y: 65 },
                                        { x: "575c0ac0", y: 48 },
                                        { x: "b20ba076", y: 46 },
                                        { x: "aff05423", y: 44 },
                                        { x: "0987bfa1", y: 42 }
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
                        <div style={{whiteSpace: "pre-line"}}>{data_analyse}</div>
                    </ExpandableSection>
                    <ExpandableSection
                        variant="footer"
                        headerText="SQL">
                        <div className={styles.sql}>
                            <SyntaxHighlighter language="javascript">
                                {sql}
                            </SyntaxHighlighter>
                            <div style={{whiteSpace: "pre-line"}}>{sql_gen_process}</div>
                        </div>
                    </ExpandableSection>
                </SpaceBetween>
            </Container>
        </SpaceBetween>
    );
}