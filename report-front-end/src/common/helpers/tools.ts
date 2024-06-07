import { AlertType } from "./types";

export const alertMsg = (alertTxt: string, alertType: AlertType) => {
  const patchEvent = new CustomEvent("showAlertMsg", {
    detail: {
      alertTxt,
      alertType,
    },
  });
  window.dispatchEvent(patchEvent);
};