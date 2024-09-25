import { Divider } from "@aws-amplify/ui-react";
import {
  Button,
  Drawer,
  FormField,
  Grid,
  Input,
  Select,
  Slider,
  SpaceBetween,
  Toggle,
} from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useDispatch, useSelector } from "react-redux";
import { getSelectData } from "../../utils/api/API";
import {
  ActionType,
  LLMConfigState,
  UserState,
} from "../../utils/helpers/types";
import "./style.scss";

const PanelConfigs = ({
  setToolsHide,
}: {
  setToolsHide: Dispatch<SetStateAction<boolean>>;
}) => {
  const dispatch = useDispatch();
  const queryConfig = useSelector((state: UserState) => state.queryConfig);

  const [intentChecked, setIntentChecked] = useState(queryConfig.intentChecked);
  const [complexChecked, setComplexChecked] = useState(
    queryConfig.complexChecked
  );
  const [answerInsightChecked, setAnswerInsightChecked] = useState(
    queryConfig.answerInsightChecked
  );
  const [contextWindow, setContextWindow] = useState(queryConfig.contextWindow);
  const [modelSuggestChecked, setModelSuggestChecked] = useState(
    queryConfig.modelSuggestChecked
  );
  const [temperature, setTemperature] = useState(queryConfig.temperature);
  const [topP, setTopP] = useState(queryConfig.topP);
  const [topK, setTopK] = useState(queryConfig.topK);
  const [maxLength, setMaxLength] = useState(queryConfig.maxLength);
  const [llmOptions, setLLMOptions] = useState([] as any[]);
  const [dataProOptions, setDataProOptions] = useState([] as any[]);
  const [selectedLLM, setSelectedLLM] = useState({
    label: queryConfig.selectedLLM,
    value: queryConfig.selectedLLM,
  } as any);
  const [selectedDataPro, setSelectedDataPro] = useState({
    label: queryConfig.selectedDataPro,
    value: queryConfig.selectedDataPro,
  } as any);

  useEffect(() => {
    getSelectData().then((response) => {
      const tempDataPro: SetStateAction<null> | { label: any; value: any }[] =
        [];
      response.data_profiles.forEach((item: any) => {
        tempDataPro.push({ label: item, value: item });
      });
      setDataProOptions(tempDataPro);
      if (!queryConfig?.selectedDataPro) {
        setSelectedDataPro(tempDataPro[0]);
      }

      const tempLLM: SetStateAction<null> | { label: any; value: any }[] = [];
      response.bedrock_model_ids.forEach((item: any) => {
        tempLLM.push({ label: item, value: item });
      });

      setLLMOptions(tempLLM);
      if (!queryConfig?.selectedLLM) {
        setSelectedLLM(tempLLM[0]);
      }
    });
  }, [queryConfig?.selectedDataPro, queryConfig?.selectedLLM]);

  useEffect(() => {
    const configInfo: LLMConfigState = {
      selectedLLM: selectedLLM ? selectedLLM.value : "",
      selectedDataPro: selectedDataPro ? selectedDataPro.value : "",
      intentChecked,
      complexChecked,
      answerInsightChecked,
      contextWindow,
      modelSuggestChecked,
      temperature,
      topP,
      topK,
      maxLength,
    };
    dispatch({ type: ActionType.UpdateConfig, state: configInfo });
  }, [
    selectedLLM,
    selectedDataPro,
    intentChecked,
    complexChecked,
    answerInsightChecked,
    modelSuggestChecked,
    temperature,
    topP,
    topK,
    maxLength,
    contextWindow,
    dispatch,
  ]);

  return (
    <Drawer header="Configurations">
      <SpaceBetween size="xxl">
        <SpaceBetween size="m">
          <FormField label="Large Language Model">
            <Select
              options={llmOptions}
              selectedOption={selectedLLM}
              onChange={({ detail }) => setSelectedLLM(detail.selectedOption)}
            />
          </FormField>
          <FormField label="Data Profile/Workspace">
            <Select
              options={dataProOptions}
              selectedOption={selectedDataPro}
              onChange={({ detail }) =>
                setSelectedDataPro(detail.selectedOption)
              }
            />
          </FormField>
        </SpaceBetween>

        <Divider label="Query Configuration" />

        <SpaceBetween size="s">
          <Toggle
            onChange={({ detail }) => setIntentChecked(detail.checked)}
            checked={intentChecked}
          >
            Query Intention Recognition and Entity Recognition
          </Toggle>
          <Toggle
            onChange={({ detail }) => setComplexChecked(detail.checked)}
            checked={complexChecked}
          >
            Complex business Query Chain-of-Thought
          </Toggle>
          <Toggle
            onChange={({ detail }) => setModelSuggestChecked(detail.checked)}
            checked={modelSuggestChecked}
          >
            Model suggestion Query
          </Toggle>
          <Toggle
            onChange={({ detail }) => setAnswerInsightChecked(detail.checked)}
            checked={answerInsightChecked}
          >
            Answer with Insights
          </Toggle>

          <FormField label="Context window">
            <div className="input-wrapper">
              <Input
                type="number"
                inputMode="numeric"
                value={contextWindow?.toString()}
                onChange={({ detail }) => {
                  if (Number(detail.value) > 10 || Number(detail.value) < 0) {
                    return;
                  }
                  setContextWindow(Number(detail.value));
                }}
                controlId="maxlength-input"
                step={1}
              />
            </div>
            <div className="flex-wrapper">
              <div className="slider-wrapper">
                <Slider
                  onChange={({ detail }) => setContextWindow(detail.value)}
                  value={contextWindow}
                  max={10}
                  min={0}
                  step={1}
                />
              </div>
            </div>
          </FormField>
        </SpaceBetween>

        <Divider label="Model Configuration" />

        <SpaceBetween size="xs">
          <Grid
            gridDefinition={[
              { colspan: { default: 6, xxs: 12 } },
              { colspan: { default: 1, xxs: 0 } },
              { colspan: { default: 5, xxs: 12 } },
            ]}
          >
            <FormField label="Temperature">
              <div className="input-wrapper">
                <Input
                  type="number"
                  inputMode="decimal"
                  value={temperature?.toString()}
                  onChange={({ detail }) => {
                    if (Number(detail.value) > 1 || Number(detail.value) < 0) {
                      return;
                    }
                    setTemperature(Number(detail.value));
                  }}
                  controlId="temperature-input"
                  step={0.1}
                />
              </div>
              <div className="flex-wrapper">
                <div className="slider-wrapper">
                  <Slider
                    onChange={({ detail }) => setTemperature(detail.value)}
                    value={temperature}
                    max={1}
                    min={0}
                    step={0.1}
                    valueFormatter={(e) => e.toFixed(1)}
                  />
                </div>
              </div>
            </FormField>

            <VerticalDivider />

            <FormField label="Top P">
              <div className="input-wrapper">
                <Input
                  type="number"
                  inputMode="numeric"
                  value={topP?.toString()}
                  onChange={({ detail }) => {
                    if (Number(detail.value) > 1 || Number(detail.value) < 0) {
                      return;
                    }
                    setTopP(Number(detail.value));
                  }}
                  controlId="top-input"
                  step={0.001}
                />
              </div>
              <div className="flex-wrapper">
                <div className="slider-wrapper">
                  <Slider
                    onChange={({ detail }) => setTopP(detail.value)}
                    value={topP}
                    max={1}
                    min={0}
                    step={0.001}
                    valueFormatter={(e) => e.toFixed(3)}
                  />
                </div>
              </div>
            </FormField>
          </Grid>

          <Grid
            gridDefinition={[
              { colspan: { default: 6, xxs: 12 } },
              { colspan: { default: 1, xxs: 0 } },
              { colspan: { default: 5, xxs: 12 } },
            ]}
          >
            <FormField label="Max Length">
              <div className="input-wrapper">
                <Input
                  type="number"
                  inputMode="numeric"
                  value={maxLength?.toString()}
                  onChange={({ detail }) => {
                    if (
                      Number(detail.value) > 2048 ||
                      Number(detail.value) < 1
                    ) {
                      return;
                    }
                    setMaxLength(Number(detail.value));
                  }}
                  controlId="maxlength-input"
                  step={1}
                />
              </div>
              <div className="flex-wrapper">
                <div className="slider-wrapper">
                  <Slider
                    onChange={({ detail }) => setMaxLength(detail.value)}
                    value={maxLength}
                    max={2048}
                    min={1}
                    step={1}
                  />
                </div>
              </div>
            </FormField>

            <VerticalDivider />

            <FormField label="Top K">
              <div className="input-wrapper">
                <Input
                  type="number"
                  inputMode="numeric"
                  value={topK?.toString()}
                  onChange={({ detail }) => {
                    if (
                      Number(detail.value) > 500 ||
                      Number(detail.value) < 0
                    ) {
                      return;
                    }
                    setTopK(Number(detail.value));
                  }}
                  controlId="topk-input"
                  step={1}
                />
              </div>
              <div className="flex-wrapper">
                <div className="slider-wrapper">
                  <Slider
                    onChange={({ detail }) => setTopK(detail.value)}
                    value={topK}
                    max={500}
                    min={0}
                    step={1}
                  />
                </div>
              </div>
            </FormField>
          </Grid>
        </SpaceBetween>

        <Button
          variant="primary"
          iconName="status-positive"
          onClick={() => {
            const configInfo: LLMConfigState = {
              selectedLLM: selectedLLM ? selectedLLM.value : "",
              selectedDataPro: selectedDataPro ? selectedDataPro.value : "",
              intentChecked,
              complexChecked,
              answerInsightChecked,
              contextWindow,
              modelSuggestChecked,
              temperature,
              topP,
              topK,
              maxLength,
            };
            dispatch({ type: ActionType.UpdateConfig, state: configInfo });
            setToolsHide(true);
            toast.success("Configuration saved");
          }}
        >
          Save
        </Button>
      </SpaceBetween>
    </Drawer>
  );
};
export default PanelConfigs;

function VerticalDivider() {
  return (
    <div
      style={{
        borderLeft: "1px solid silver",
        width: "1px",
        height: "80%",
        margin: "0 auto",
      }}
    />
  );
}
