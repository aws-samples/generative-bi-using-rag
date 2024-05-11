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
import "./style.scss";
import { BACKEND_URL } from "../../tools/const";
import { alertMsg } from "../../tools/tool";
import { ActionType, UserState } from "../../types/StoreTypes";
import { useSelector, useDispatch } from "react-redux";

const ConfigPanel = () => {
  const userInfo = useSelector<UserState>((state) => state) as UserState;
  const dispatch = useDispatch();
  const [intentChecked, setIntentChecked] = useState(true);
  const [complexChecked, setComplexChecked] = useState(true);
  const [modelSuggestChecked, setModelSuggestChecked] = useState(true);
  const [temperature, setTemperature] = useState(1);
  const [topP, setTopP] = useState(0.999);
  const [topK, setTopK] = useState(250);
  const [maxLength, setMaxLength] = useState(2048);
  const [loading, setLoading] = useState(false);
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
    getSelectData();
  }, []);

  const getSelectData = async () => {
    setLoading(true);
    try {
      const reponse = await fetch(`${BACKEND_URL}qa/option`, {
        method: "GET",
      });
      if (!reponse.ok) {
        alertMsg("LLM Option Error", "error");
        return;
      }
      const result = await reponse.json();

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
    setLoading(false);
  };

  useEffect(() => {
    updateCache(
      selectedLLM,
      selectedDataPro,
      intentChecked,
      complexChecked,
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
    <HelpPanel header="Configuration" loading={loading}>
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
              step={0.01}
            />
          </div>
          <div className="flex-wrapper">
            <div className="slider-wrapper">
              <Slider
                onChange={({ detail }) => setTemperature(detail.value)}
                value={temperature}
                max={1}
                min={0}
                step={0.01}
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
                if (Number(detail.value) > 0.999 || Number(detail.value) < 0) {
                  return;
                }
                setTopP(Number(detail.value));
              }}
              controlId="topp-input"
              step={0.001}
            />
          </div>
          <div className="flex-wrapper">
            <div className="slider-wrapper">
              <Slider
                onChange={({ detail }) => setTopP(detail.value)}
                value={topP}
                max={0.999}
                min={0}
                step={0.001}
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
