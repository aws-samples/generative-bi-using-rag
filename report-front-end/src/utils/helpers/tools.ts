import { User } from "oidc-client-ts";
import { LOCAL_STORAGE_KEYS } from "../constants";

export function getOidcUser() {
  const oidcStorage = localStorage.getItem(LOCAL_STORAGE_KEYS.oidcUser);
  return oidcStorage ? User.fromStorageString(oidcStorage) : null;
}

export const dispatchUnauthorizedEvent = () => {
  window.dispatchEvent(new CustomEvent("unauthorized"));
};
