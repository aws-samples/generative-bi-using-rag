import {
  ChatBotHistoryItem,
  ChatBotMessageType,
  FeedBackItem,
  SessionItem,
} from "../../components/chatbot-panel/types";
import { Dispatch, SetStateAction } from "react";
import {
  BACKEND_URL,
  DEFAULT_QUERY_CONFIG,
  LOCAL_STORAGE_KEYS,
} from "../constant/constants";
import { alertMsg } from "../helpers/tools";
import { extend } from "umi-request";

export const getLSTokens = () => {
  const accessToken =
    localStorage.getItem(LOCAL_STORAGE_KEYS.accessToken) || "";
  const idToken = localStorage.getItem(LOCAL_STORAGE_KEYS.idToken) || "";
  const refreshToken =
    localStorage.getItem(LOCAL_STORAGE_KEYS.refreshToken) || "";

  return {
    accessToken: `Bearer ${accessToken}`,
    idToken: `Bearer ${idToken}`,
    refreshToken: `Bearer ${refreshToken}`,
    noToken: !accessToken || !idToken || !refreshToken,
  };
};
export const getBearerTokenObj = () => {
  const { accessToken, idToken, refreshToken } = getLSTokens();
  return {
    "Authorization": accessToken,
    "X-Access-Token": accessToken,
    "X-Id-Token": idToken,
    "X-Refresh-Token": refreshToken,
  };
};

export const request = extend({
  prefix: BACKEND_URL,
  timeout: 30 * 1000,
  headers: { "Content-Type": "application/json" },
});

request.interceptors.request.use((url, options) => {
  return {
    url,
    options: {
      ...options,
      headers: { ...getBearerTokenObj(), ...options.headers },
    },
  };
});

request.interceptors.response.use((response) => {
  if (response.status === 401) {
    const patchEvent = new CustomEvent("unauthorized", {
      detail: {},
    });
    window.dispatchEvent(patchEvent);
    // window.location.href = "/login";
  }
  return response;
});

export async function getSelectData() {
  try {
    const data = await request.get(`qa/option`, {
      errorHandler: (error) => {
        alertMsg("LLM Option Error", "error");
        console.error("LLM Option Error: ", error);
      },
    });
    if (!data || !data.data_profiles || !data.bedrock_model_ids) {
      alertMsg("LLM Option Error: data missing", "error");
      return;
    }
    return data;
  } catch (error) {
    console.error("getSelectData Error", error);
  }
}

export const getRecommendQuestions = async (data_profile: string) => {
  try {
    const data = await request.get("qa/get_custom_question", {
      params: { data_profile },
      errorHandler: (error) => {
        alertMsg("getCustomQuestions response error", "error");
        console.error("getCustomQuestions response error, ", error);
      },
    });
    return data.custom_question;
  } catch (error) {
    console.error("getCustomQuestions Error", error);
  }
};
export async function addUserFeedback(feedbackData: FeedBackItem) {
  // call api
  try {
    const data = await request.post("qa/user_feedback", {
      data: feedbackData,
      errorHandler: (error) => {
        alertMsg("AddUserFeedback", "error");
        console.error("AddUserFeedback error, ", error);
      },
    });
    alertMsg("Thanks for your feedback!", "success");
    console.log("AddUserFeedback: ", data);
    return data;
  } catch (err) {
    console.error("Query error, ", err);
  }
}

export async function getSessions(sessionItem: SessionItem) {
  try {
    const data = await request.post("qa/get_history_by_user_profile", {
      data: sessionItem,
      errorHandler: (error) => {
        alertMsg("getSessions", "error");
        console.error("getSessions, error: ", error);
      },
    });
    return data;
  } catch (error) {
    console.error("getSessions, error: ", error);
  }
}

/**
 * @deprecated replaced by websocket query method
 */
export async function query(props: {
  query: string;
  setLoading: Dispatch<SetStateAction<boolean>>;
  configuration: any;
  setMessageHistory: Dispatch<SetStateAction<ChatBotHistoryItem[]>>;
}) {
  props.setMessageHistory((history: ChatBotHistoryItem[]) => {
    return [
      ...history,
      {
        type: ChatBotMessageType.Human,
        content: props.query,
      },
    ];
  });
  props.setLoading(true);
  try {
    const data = await request.post("qa/ask", {
      data: {
        query: props.query,
        bedrock_model_id:
          props.configuration.selectedLLM || DEFAULT_QUERY_CONFIG.selectedLLM,
        use_rag_flag: true,
        visualize_results_flag: true,
        intent_ner_recognition_flag: props.configuration.intentChecked,
        agent_cot_flag: props.configuration.complexChecked,
        profile_name:
          props.configuration.selectedDataPro ||
          DEFAULT_QUERY_CONFIG.selectedDataPro,
        explain_gen_process_flag: true,
        gen_suggested_question_flag: props.configuration.modelSuggestChecked,
        answer_with_insights:
          props.configuration.answerInsightChecked ||
          DEFAULT_QUERY_CONFIG.answerInsightChecked,
        top_k: props.configuration.topK,
        top_p: props.configuration.topP,
        max_tokens: props.configuration.maxLength,
        temperature: props.configuration.temperature,
      },
      errorHandler: (error) => console.error("Query error, ", error),
    });
    console.log("http query response: ", data);
    props.setLoading(false);
    props.setMessageHistory((history: ChatBotHistoryItem[]) => {
      return [
        ...history,
        {
          type: ChatBotMessageType.AI,
          content: data,
        },
      ];
    });
  } catch (err) {
    props.setLoading(false);
    const result = {
      query: props.query,
      query_intent: "Error",
      knowledge_search_result: {},
      sql_search_result: [],
      agent_search_result: {},
      suggested_question: [],
    };
    props.setLoading(false);
    props.setMessageHistory((history: any) => {
      return [
        ...history,
        {
          type: ChatBotMessageType.AI,
          content: result,
        },
      ];
    });
    console.error("Query error, ", err);
  }
}
