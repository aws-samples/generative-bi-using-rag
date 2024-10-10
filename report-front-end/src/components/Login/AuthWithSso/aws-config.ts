export const awsConfig = {
  Auth: {
    region: process.env.VITE_COGNITO_REGION,
    userPoolId: process.env.VITE_COGNITO_USER_POOL_ID,
    userPoolWebClientId: process.env.VITE_COGNITO_USER_POOL_WEB_CLIENT_ID,
    // Extra configs for SSO login
    mandatorySignIn: false,
    authenticationFlowType: "USER_SRP_AUTH",
    oauth: {
      domain: import.meta.env.VITE_SSO_OAUTH_DOMAIN,
      scope: ["email", "openid", "aws.cognito.signin.user.admin", "profile"],
      redirectSignIn: window.location.origin,
      redirectSignOut: window.location.origin,
      responseType: "code",
    },
  },
};
