export const awsConfig = {
    Auth: {
        region: process.env.VITE_COGNITO_REGION,
        userPoolId: process.env.VITE_COGNITO_USER_POOL_ID,
        userPoolWebClientId: process.env.VITE_COGNITO_USER_POOL_WEB_CLIENT_ID,
    }
};
