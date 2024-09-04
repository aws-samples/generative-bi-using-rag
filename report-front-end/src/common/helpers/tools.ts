import { Auth } from "aws-amplify";
import toast from "react-hot-toast";
import { LOCAL_STORAGE_KEYS } from "../constant/constants";

export const logout = () => {
  console.warn("Not authorized! Logging out");
  toast.error("Please login first!");
  Object.keys(LOCAL_STORAGE_KEYS).forEach((key) =>
    localStorage.removeItem(key)
  );
  Auth.signOut();
};

/**
 * @deprecated please use logout() function directly
 */
export const dispatchUnauthorizedEvent = () => {
  window.dispatchEvent(new CustomEvent("unauthorized"));
};
