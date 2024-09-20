import toast from "react-hot-toast";
import { extend } from "umi-request";
import { Session } from "../../components/PanelSideNav/types";
import {
  FeedBackItem,
  HistoryItem,
  SessionItem,
} from "../../components/SectionChat/types";
import {
  AUTH_WITH_NOTHING,
  BACKEND_URL,
  LOCAL_STORAGE_KEYS,
} from "../constants";
import { dispatchUnauthorizedEvent } from "../helpers/tools";

export const getLSTokens = () => {
  const accessToken =
    localStorage.getItem(LOCAL_STORAGE_KEYS.accessToken) || "";
  const idToken = localStorage.getItem(LOCAL_STORAGE_KEYS.idToken) || "";
  const refreshToken =
    localStorage.getItem(LOCAL_STORAGE_KEYS.refreshToken) || "";

  return {
    accessToken: `Bearer ${accessToken}`,
    idToken: `Bearer ${idToken}`,
    refreshToken: refreshToken ? `Bearer ${refreshToken}` : '',
    noToken: !accessToken || !idToken || !refreshToken,
  };
};
export const getBearerTokenObj = () => {
  const { accessToken, idToken, refreshToken } = getLSTokens();
  return {
    // Authorization: accessToken,
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
  if (AUTH_WITH_NOTHING) return { url, options };
  const headers = { ...getBearerTokenObj(), ...options.headers };
  return { url, options: { ...options, headers } };
});

request.interceptors.response.use((response) => {
  if (response.status === 500) toast.error(`Internal Server Error: 500`);
  if (AUTH_WITH_NOTHING) return response;
  if (response.status === 401) dispatchUnauthorizedEvent();
  return response;
});

export async function getSelectData() {
  try {
    const data = await request.get(`qa/option`, {
      errorHandler: (error) => {
        toast.error("LLM Option Error");
        console.error("LLM Option Error: ", error);
      },
    });
    if (!data || !data.data_profiles || !data.bedrock_model_ids) {
      toast.error("LLM Option Error: data missing");
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
        toast.error("getCustomQuestions response error");
        console.error("getCustomQuestions response error, ", error);
      },
    });
    return data.custom_question;
  } catch (error) {
    console.error("getCustomQuestions Error", error);
  }
};
export async function postUserFeedback(feedbackData: FeedBackItem) {
  try {
    const data = await request.post("qa/user_feedback", {
      data: feedbackData,
      errorHandler: (error) => {
        toast.error("AddUserFeedback");
        console.error("AddUserFeedback error, ", error);
      },
    });
    toast.success("Thanks for your feedback!");
    console.log("AddUserFeedback: ", data);
    return data;
  } catch (err) {
    console.error("Query error, ", err);
  }
}

export async function getSessions(sessionItem: SessionItem) {
  try {
    const data = await request.post(`qa/get_sessions`, {
      data: sessionItem,
      errorHandler: (error) => {
        toast.error("getSessions error");
        console.error("getSessions error: ", error);
      },
    });
    return data as Session[];
  } catch (error) {
    console.error("getSessions, error: ", error);
    return [];
  }
}

export async function deleteHistoryBySession(historyItem: HistoryItem) {
  try {
    const data = await request.post(`qa/delete_history_by_session`, {
      data: historyItem,
      errorHandler: (error) => {
        toast.error("deleteHistoryBySession error");
        console.error("deleteHistoryBySession error: ", error);
      },
    });
    return data;
  } catch (error) {
    console.error("deleteHistoryBySession, error: ", error);
  }
}

export async function getHistoryBySession(historyItem: HistoryItem) {
  // call api
  try {
    const data = await request.post(`qa/get_history_by_session`, {
      data: historyItem,
      errorHandler: (error) => {
        toast.error("getHistoryBySession error");
        console.error("getHistoryBySession error: ", error);
      },
    });
    return data;
  } catch (error) {
    console.error("getHistoryBySession, error: ", error);
  }
}
