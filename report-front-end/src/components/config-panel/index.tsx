import {
  FormField,
  HelpPanel,
  Input,
  Select,
  Slider,
  SpaceBetween,
  Toggle,
} from "@cloudscape-design/components";
import { SetStateAction, useEffect, useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { BACKEND_URL } from "../../common/constant/constants";
import { alertMsg } from "../../common/helpers/tools";
import "./style.scss";
import { ActionType, UserState } from "../../common/helpers/types";

const ConfigPanel = () => {
  const userInfo = useSelector<UserState>((state) => state) as UserState;
  const dispatch = useDispatch();
  const [intentChecked, setIntentChecked] = useState(true);
  const [complexChecked, setComplexChecked] = useState(true);
  const [answerInsightChecked, setAnswerInsightChecked] = useState(false);
  const [contextWindow, setContextWindow] = useState(false);
  const [modelSuggestChecked, setModelSuggestChecked] = useState(false);
  const [temperature, setTemperature] = useState(0.01);
  const [topP, setTopP] = useState(0.999);
  const [topK, setTopK] = useState(250);
  const [maxLength, setMaxLength] = useState(2048);
  const [llmOptions, setLLMOptions] = useState([] as any[]);
  const [dataProOptions, setDataProOptions] = useState([] as any[]);
  const [selectedLLM, setSelectedLLM] = useState({
    label: "",
    value: "",
  } as any);
  const [selectedDataPro, setSelectedDataPro] = useState({
    label: "",
    value: "",
  } as any);

  useEffect(() => {
    getSelectData().then();
  }, []);

  const getSelectData = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}qa/option`, {
        method: "GET",
      });
      if (!response.ok) {
        alertMsg("LLM Option Error", "error");
        return;
      }
      const result = await response.json();
      if (!result || !result.data_profiles || !result.bedrock_model_ids) {
        alertMsg("LLM Option Error", "error");
        return;
      }
      const tempDataPro: SetStateAction<null> | { label: any; value: any }[] =
        [];
      result.data_profiles.forEach((item: any) => {
        tempDataPro.push({ label: item, value: item });
      });
      setDataProOptions(tempDataPro);
      setSelectedDataPro(tempDataPro[0]);

      const tempLLM: SetStateAction<null> | { label: any; value: any }[] = [];
      result.bedrock_model_ids.forEach((item: any) => {
        tempLLM.push({ label: item, value: item });
      });

      setLLMOptions(tempLLM);
      setSelectedLLM(tempLLM[0]);
    } catch (error) {
      console.error("getSelectData Error", error);
    }
  };

  useEffect(() => {
    updateCache(
      selectedLLM,
      selectedDataPro,
      intentChecked,
      complexChecked,
      answerInsightChecked,
      modelSuggestChecked,
      temperature,
      topP,
      topK,
      maxLength
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
  ]);

  const updateCache = (
    selectedLLM: any,
    selectedDataPro: any,
    intentChecked: boolean,
    complexChecked: boolean,
    answerInsightChecked: boolean,
    modelSuggestChecked: boolean,
    temperature: number,
    topP: number,
    topK: number,
    maxLength: number
  ) => {
    const configInfo: UserState = {
      ...userInfo,
      queryConfig: {
        selectedLLM: selectedLLM ? selectedLLM.value : "",
        selectedDataPro: selectedDataPro ? selectedDataPro.value : "",
        intentChecked,
        complexChecked,
        answerInsightChecked,
        modelSuggestChecked,
        temperature,
        topP,
        topK,
        maxLength,
      },
    };
    dispatch({ type: ActionType.UpdateConfig, state: configInfo });
  };

  return (
    <HelpPanel header="Configuration">
      <SpaceBetween size="l">
        <FormField label="LLM" description="Select a large language model">
          <Select
            options={llmOptions}
            selectedOption={selectedLLM}
            onChange={({ detail }) => setSelectedLLM(detail.selectedOption)}
          ></Select>
        </FormField>
        <FormField
          label="Data Profile"
          description="Select a profile/workspace"
        >
          <Select
            options={dataProOptions}
            selectedOption={selectedDataPro}
            onChange={({ detail }) => setSelectedDataPro(detail.selectedOption)}
          ></Select>
        </FormField>
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
        <Toggle
          onChange={({ detail }) => setContextWindow(detail.checked)}
          checked={contextWindow}
        >
          Context window
        </Toggle>

        <FormField label="Temperature">
          <div className="input-wrapper">
            <Input
              type="number"
              inputMode="decimal"
              value={temperature.toString()}
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
                valueFormatter={(e) => e.toFixed(2)}
              />
            </div>
          </div>
        </FormField>

        <FormField label="Top P">
          <div className="input-wrapper">
            <Input
              type="number"
              inputMode="numeric"
              value={topP.toString()}
              onChange={({ detail }) => {
                if (Number(detail.value) > 1 || Number(detail.value) < 0) {
                  return;
                }
                setTopP(Number(detail.value));
              }}
              controlId="topp-input"
              step={0.1}
            />
          </div>
          <div className="flex-wrapper">
            <div className="slider-wrapper">
              <Slider
                onChange={({ detail }) => setTopP(detail.value)}
                value={topP}
                max={1}
                min={0}
                step={0.1}
                valueFormatter={(e) => e.toFixed(3)}
              />
            </div>
          </div>
        </FormField>

        <FormField label="Top K">
          <div className="input-wrapper">
            <Input
              type="number"
              inputMode="numeric"
              value={topK.toString()}
              onChange={({ detail }) => {
                if (Number(detail.value) > 500 || Number(detail.value) < 0) {
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

        <FormField label="Maximum Length">
          <div className="input-wrapper">
            <Input
              type="number"
              inputMode="numeric"
              value={maxLength.toString()}
              onChange={({ detail }) => {
                if (Number(detail.value) > 8192 || Number(detail.value) < 1) {
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
                max={8192}
                min={1}
                step={1}
              />
            </div>
          </div>
        </FormField>
      </SpaceBetween>
    </HelpPanel>
  );
};
export default ConfigPanel;
