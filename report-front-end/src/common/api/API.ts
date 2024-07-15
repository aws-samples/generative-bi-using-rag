import { FeedBackItem } from "../../components/chatbot-panel/types";
import { BACKEND_URL } from "../constant/constants";
import axios from "axios";
import { Dispatch, SetStateAction } from "react";

const instance = axios.create();

instance.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    if (error.response.status === 401) {
      const patchEvent = new CustomEvent("unauthorized", {
        detail: {},
      });
      window.dispatchEvent(patchEvent);
    } else {
      return Promise.reject(error);
    }
  },
);

export async function getRecommendQuestions(data_profile: string, setQuestions: Dispatch<SetStateAction<string[]>>) {
  instance.get(`${BACKEND_URL}qa/get_custom_question?data_profile=${data_profile}`, {
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
    return await instance.get(`${BACKEND_URL}qa/option`, {
      timeout: 5000,
    });
  } catch (error) {
    console.error("getSelectData Error", error);
  }
}

export async function addUserFeedback(feedbackData: FeedBackItem) {
  try {
    return await instance.post(`${BACKEND_URL}qa/user_feedback`, {
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