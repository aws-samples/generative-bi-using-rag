import { FeedBackItem, SessionItem } from "../../components/chatbot-panel/types";
import { BACKEND_URL } from "../constant/constants";
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