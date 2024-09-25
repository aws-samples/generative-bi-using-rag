import AuthWithAzureAd from "./AuthWithAzureAd";
import AuthWithCognito from "./AuthWithCognito";
import AuthWithNothing from "./AuthWithNothing";
import AuthWithOidc from "./AuthWithOidc";
import AuthWithSso from "./AuthWithSso";

const Login = {
  Cognito: AuthWithCognito,
  Sso: AuthWithSso,
  Oidc: AuthWithOidc,
  AzureAd: AuthWithAzureAd,
  Custom: AuthWithNothing,
};

export default Login;
