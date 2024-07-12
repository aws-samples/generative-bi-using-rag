import { FeedBackItem } from "../../components/chatbot-panel/types";
import { BACKEND_URL } from "../constant/constants";
import request from "umi-request";

// handling error in response interceptor
request.interceptors.response.use(response => {
  if (response.status === 401) {
    const patchEvent = new CustomEvent("unauthorized", {
      detail: {},
    });
    window.dispatchEvent(patchEvent);
  }
  return response;
});

export async function getSelectData() {
  try {
    return await request.get(`${BACKEND_URL}qa/option`, {
      timeout: 5000
    });
  } catch (error) {
    console.error("getSelectData Error", error);
  }
}

export async function addUserFeedback(feedbackData: FeedBackItem) {
  try {
    return await request.post(`${BACKEND_URL}qa/user_feedback`, {
      timeout: 5000,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(feedbackData),
    });
  } catch (error) {
    console.error("Query error, ", error);
  }
}