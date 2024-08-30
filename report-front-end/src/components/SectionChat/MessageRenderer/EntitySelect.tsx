import {
  Box,
  Button,
  RadioGroup,
  SpaceBetween,
} from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { useQueryWithTokens } from "../../../utils/api/WebSocket";
import { IEntityItem, QUERY_INTENT } from "../types";
import { IPropsAiMessageRenderer } from "./AiMessage";

export default function EntitySelect({
  content,
  sendJsonMessage,
}: IPropsAiMessageRenderer) {
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
