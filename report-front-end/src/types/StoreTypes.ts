export enum ActionType {
  Update = "Update",
  Delete = "Delete",
  UpdateConfig = "UpdateConfig",
}

export type UserState = {
  userId: string;
  account: string;
  displayName: string;
  email: string;
  loginExpiration: number;
  queryConfig: any;
};

export type UserAction = { type: ActionType; state?: any };
