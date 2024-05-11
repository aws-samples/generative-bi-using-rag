import { ChatBotHistoryItem } from "@/components/chatbot/types";
import { Dispatch, SetStateAction } from "react";
import { BACKEND_URL } from "../tools/const";

export interface QueryProps {
  query: string;
  setLoading: Dispatch<SetStateAction<boolean>>;
  configuration: any;
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
}

export async function query(props: QueryProps) {
  props.setLoading(true);
  try {
    const param = {
      query: props.query,
      bedrock_model_id: props.configuration.selectedLLM,
      use_rag_flag: true,
      visualize_results_flag: true,
      intent_ner_recognition_flag: props.configuration.intentChecked,
      agent_cot_flag: props.configuration.complexChecked,
      profile_name: props.configuration.selectedDataPro,
      explain_gen_process_flag: true,
      gen_suggested_question_flag: props.configuration.modelSuggestChecked,
      top_k: props.configuration.topK,
      top_p: props.configuration.topP,
      max_tokens: props.configuration.maxLength,
      temperature: props.configuration.temperature
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
      knowledge_search_result: {},
      sql_search_result: [],
      agent_search_result: {},
      suggested_question: []
    };
    props.setLoading(false);
    props.setMessageHistory((history: any) => {
      return [...history, result];
    });
    console.error('Query error, ', err);
  }
}
