export type AlertType = "error" | "warning" | "info" | "success";

export const COMMON_ALERT_TYPE = {
  Success: "success",
  Error: "error",
  Warning: "warning",
  Info: "info",
};

export interface CommonAlertProps {
  alertTxt: string;
  alertType: AlertType;
}

export enum ActionType {
  Update = "Update",
  Delete = "Delete",
  UpdateConfig = "UpdateConfig",
}

export type UserState = {
  userId: string;
  displayName: string;
  email: string;
  loginExpiration: number;
  queryConfig: any;
};

export type UserAction = { type: ActionType; state?: any };