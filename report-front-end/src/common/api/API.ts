import { FeedBackItem, HistoryItem, SessionItem } from "../../components/chatbot-panel/types";
import axios from "axios";
import { Dispatch, SetStateAction } from "react";

const instance = axios.create();

instance.interceptors.response.use(
  (response) => {
    if (response.headers && response.headers["x-user-id"]) {
      const patchEvent = new CustomEvent("authorized", {
        detail: {
          userId: response.headers["x-user-id"],
          userName: response.headers["x-user-name"],
        },
      });
      window.dispatchEvent(patchEvent);
    }
    return response.data;
  },
  (error) => {
    if (error.response && error.response.status) {
      if (error.response.status === 401) {
        const patchEvent = new CustomEvent("unauthorized", {
          detail: {},
        });
        window.dispatchEvent(patchEvent);
      } else {
        return Promise.reject(error);
      }
    }
  },
);

export async function getRecommendQuestions(data_profile: string, setQuestions: Dispatch<SetStateAction<string[]>>) {
  instance.get(`/api/qa/get_custom_question?data_profile=${data_profile}`, {
    timeout: 5000,
  }).then((response: any) => {
    if (response) {
      const custom_question = response["custom_question"];
      if (custom_question) {
        setQuestions(custom_question);
      }
    }
  }).catch((error) => {
    console.log(error);
  });
}

export async function getSelectData() {
  try {
    return await instance.get(`/api/qa/option`, {
      timeout: 5000,
    });
  } catch (error) {
    console.error("getSelectData Error", error);
  }
}

export async function addUserFeedback(feedbackData: FeedBackItem) {
  try {
    return await instance.post(`/api/qa/user_feedback`, JSON.stringify(feedbackData), {
      timeout: 5000,
      headers: {
        "Content-Type": "application/json",
      },
    });
  } catch (error) {
    console.error("Query error, ", error);
  }
}

export async function getHistory(sessionItem: SessionItem) {
  // call api
  try {
    const response = await fetch(`/api/qa/get_history_by_user_profile`, {
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
    console.error("getHistory, error: ", error);
  }
}

export async function getSessions(sessionItem: SessionItem) {
  // call api
  try {
    const response = await fetch(`/api/qa/get_sessions`, {
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

export async function deleteHistoryBySession(historyItem: HistoryItem) {
  // call api
  try {
    const response = await fetch(`/api/qa/delete_history_by_session`, {
      headers: {
        "Content-Type": "application/json"
      },
      method: "POST",
      body: JSON.stringify(historyItem)
    });
    if (!response.ok) {
      return;
    }
    return await response.json();
  } catch (error) {
    console.error("deleteHistoryBySession, error: ", error);
  }
}

export async function getHistoryBySession(historyItem: HistoryItem) {
  // call api
  try {
    const response = await fetch(`/api/qa/get_history_by_session`, {
      headers: {
        "Content-Type": "application/json"
      },
      method: "POST",
      body: JSON.stringify(historyItem)
    });
    if (!response.ok) {
      return;
    }
    return await response.json();
  } catch (error) {
    console.error("getHistoryBySession, error: ", error);
  }
}