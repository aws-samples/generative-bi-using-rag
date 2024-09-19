import AuthWithCognito from "./AuthWithCognito";
import AuthWithNothing from "./AuthWithNothing";
import OidcLogin from "./AuthWithOidc";
import AuthWithSso from "./AuthWithSso";

const Login = {
  Cognito: AuthWithCognito,
  Sso: AuthWithSso,
  Oidc: OidcLogin,
  Custom: AuthWithNothing,
};

export default Login;
