export const awsConfig = {
    Auth: {
        region: import.meta.env.VITE_COGNITO_REGION,
        userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
        userPoolWebClientId: import.meta.env.VITE_COGNITO_USER_POOL_WEB_CLIENT_ID,
    }
};
