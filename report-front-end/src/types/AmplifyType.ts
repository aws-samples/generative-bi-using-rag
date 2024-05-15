export interface AmplifyConfigType {
  aws_api_key: string;
  aws_project_region: string;
  aws_appsync_graphqlEndpoint: string;
  aws_appsync_region: string;
  aws_appsync_authenticationType: string;
  aws_cognito_region: string;
  aws_user_pools_id: string;
  aws_user_pools_web_client_id: string;
  aws_monitoring_url: string;
  aws_monitoring_api_key: string;
  aws_monitoring_stack_name: string;
  aws_user_pools_web_client_secret?: string;
}

// export enum ActionType {
//   UPDATE_AMPLIFY_CONFIG,
// }

// export type Action = {
//   type: ActionType.UPDATE_AMPLIFY_CONFIG;
//   amplifyConfig: AmplifyConfigType;
// };

// export interface AppStateProps {
//   amplifyConfig: any;
// }

// const initialState: AppStateProps = {
//   amplifyConfig: {},
// };

// export const AppReducer = (
//   state = initialState,
//   action: Action
// ): AppStateProps => {
//   switch (action.type) {
//     case ActionType.UPDATE_AMPLIFY_CONFIG:
//       return { ...state, amplifyConfig: action.amplifyConfig };

//     default:
//       return state;
//   }
// };
