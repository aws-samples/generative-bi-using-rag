import {
  ChatBotHistoryItem,
  ChatBotMessageType,
  FeedBackItem,
  SessionItem,
} from "../../components/chatbot-panel/types";
import { Dispatch, SetStateAction } from "react";
import { BACKEND_URL, DEFAULT_QUERY_CONFIG } from "../constant/constants";
import { alertMsg } from "../helpers/tools";

export async function getSelectData() {
  // call api
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
    return result;

  } catch (error) {
    console.error("getSelectData Error", error);
  }
}

export async function query(props: {
  query: string;
  setLoading: Dispatch<SetStateAction<boolean>>;
  configuration: any;
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
}) {
  props.setMessageHistory((history: ChatBotHistoryItem[]) => {
    return [...history, {
      type: ChatBotMessageType.Human,
      content: props.query
    }];
  });
  props.setLoading(true);
  try {
    const param = {
      query: props.query,
      bedrock_model_id: props.configuration.selectedLLM || DEFAULT_QUERY_CONFIG.selectedLLM,
      use_rag_flag: true,
      visualize_results_flag: true,
      intent_ner_recognition_flag: props.configuration.intentChecked,
      agent_cot_flag: props.configuration.complexChecked,
      profile_name: props.configuration.selectedDataPro || DEFAULT_QUERY_CONFIG.selectedDataPro,
      explain_gen_process_flag: true,
      gen_suggested_question_flag: props.configuration.modelSuggestChecked,
      answer_with_insights: props.configuration.answerInsightChecked || DEFAULT_QUERY_CONFIG.answerInsightChecked,
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
    console.log("response: ", result);
    props.setLoading(false);
    props.setMessageHistory((history: ChatBotHistoryItem[]) => {
      return [...history, {
        type: ChatBotMessageType.AI,
        content: result
      }];
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
      return [...history, {
        type: ChatBotMessageType.AI,
        content: result
      }];
    });
    console.error('Query error, ', err);
  }
}

export async function addUserFeedback(feedbackData: FeedBackItem) {
  // call api
  try {
    const url = `${BACKEND_URL}qa/user_feedback`;
    const response = await fetch(url, {
        headers: {
          "Content-Type": "application/json"
        },
        method: "POST",
        body: JSON.stringify(feedbackData)
      }
    );
    if (!response.ok) {
      console.error('AddUserFeedback error, ', response);
      return;
    }
    const result = await response.json();
    console.log("AddUserFeedback: ", result);
    return result;
  } catch (err) {
    console.error('Query error, ', err);
  }
}

export async function getSessions(sessionItem: SessionItem) {
  // call api
  try {
    const response = await fetch(`${BACKEND_URL}qa/get_history_by_user_profile`, {
      headers: {
        "Content-Type": "application/json"
      },
      method: "POST",
      body: JSON.stringify(sessionItem)
    });
    if (!response.ok) {
      return;
    }
    return await response.json();
  } catch (error) {
    console.error("getSessions, error: ", error);
  }
}