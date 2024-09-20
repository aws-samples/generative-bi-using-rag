import { Auth } from "aws-amplify";
import { User } from "oidc-client-ts";
import toast from "react-hot-toast";
import { LOCAL_STORAGE_KEYS } from "../constants";

export default function getUser() {
  const oidcStorage = localStorage.getItem(LOCAL_STORAGE_KEYS.oidcUser);
  return oidcStorage ? User.fromStorageString(oidcStorage) : null;
}

export const logout = () => {
  console.warn("Not authorized! Logging out");
  toast.error("Please login first!");
  // Object.values(LOCAL_STORAGE_KEYS).forEach((key) =>
  //   localStorage.removeItem(key)
  // );
  Auth.signOut();
  // window.location.reload();
};

/**
 * @deprecated please use logout() function directly
 */
export const dispatchUnauthorizedEvent = () => {
  window.dispatchEvent(new CustomEvent("unauthorized"));
};
