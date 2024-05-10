import { ChatBotConfiguration, ChatBotHistoryItem } from "@/components/chatbot/types";
import { Dispatch, SetStateAction } from "react";
import { BACKEND_URL } from "../tools/const";

export interface QueryProps {
  query: string;
  setLoading: Dispatch<SetStateAction<boolean>>;
  configuration: ChatBotConfiguration;
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
}

export async function query_test(props: QueryProps) {
  props.setLoading(true);
  try {
    // const url = `${BACKEND_URL}qa/ask/test?question_type=reject`;
    // const url = `${BACKEND_URL}qa/ask/test?question_type=knowledge`;
    // const url = `${BACKEND_URL}qa/ask/test?question_type=normal_table`;
    // const url = `${BACKEND_URL}qa/ask/test?question_type=normal_line`;
    const url = `${BACKEND_URL}qa/ask/test?question_type=normal_pie`;
    // const url = `${BACKEND_URL}qa/ask/test?question_type=agent`;
    const response = await fetch(url, {
        headers: {
          "Content-Type": "application/json"
        },
        method: "POST",
        body: JSON.stringify({}),
      }
    );
    if (!response.ok) {
      return;
    }
    const result = await response.json();
    console.log(result);
    props.setLoading(false);
    if (result) {
      props.setMessageHistory((history: ChatBotHistoryItem[]) => {
        return [...history, result];
      });
    }
  } catch (err) {
    props.setLoading(false);
    const result = {
      query: props.query,
      query_intent: "Error",
    };
    props.setLoading(false);
    props.setMessageHistory((history: any) => {
      return [...history, result];
    });
    console.error('Query error, ', err);
  }
}

export async function query(props: QueryProps) {
  props.setLoading(true);
  try {
    /*const param = {
      query: state.value,
      bedrock_model_id: userInfo.queryConfig.selectedLLM,
      use_rag_flag: true,
      visualize_results_flag: true,
      intent_ner_recognition_flag: userInfo.queryConfig.intentChecked,
      agent_cot_flag: userInfo.queryConfig.complexChecked,
      profile_name: userInfo.queryConfig.selectedDataPro,
      explain_gen_process_flag: true,
      gen_suggested_question_flag: userInfo.queryConfig.modelSuggestChecked,
      top_k: userInfo.queryConfig.topK,
      top_p: userInfo.queryConfig.topP,
      max_tokens: userInfo.queryConfig.maxLength,
      temperature: userInfo.queryConfig.temperature
    };*/
    // For test purpose
    const param = {
      query: props.query,
      bedrock_model_id: "anthropic.claude-3-sonnet-20240229-v1:0",
      use_rag_flag: true,
      visualize_results_flag: true,
      intent_ner_recognition_flag: true,
      agent_cot_flag: true,
      profile_name: "shopping-demo",
      explain_gen_process_flag: true,
      gen_suggested_question_flag: true,
      top_k: 250,
      top_p: 0.9,
      max_tokens: 2048,
      temperature: 0.01
    };
    const url = `${BACKEND_URL}qa/ask`;
    const response = await fetch(url, {
        headers: {
          "Content-Type": "application/json"
        },
        method: "POST",
        body: JSON.stringify(param)
      }
    );
    if (!response.ok) {
      console.error('Query error, ', response);
      return;
    }
    const result = await response.json();
    console.log(result);
    props.setLoading(false);
    props.setMessageHistory((history: ChatBotHistoryItem[]) => {
      return [...history, result];
    });
  } catch (err) {
    props.setLoading(false);
    const result = {
      query: props.query,
      query_intent: "Error",
    };
    props.setLoading(false);
    props.setMessageHistory((history: any) => {
      return [...history, result];
    });
    console.error('Query error, ', err);
  }
}
