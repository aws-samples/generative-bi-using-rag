import { WebStorageStateStore } from "oidc-client-ts";
import React, { useEffect } from "react";
import { AuthProvider, useAuth } from "react-oidc-context";
import { useDispatch } from "react-redux";
import App from "../../../app";
import {
  AUTH_WITH_OIDC,
  LOCAL_STORAGE_KEYS,
  OIDC,
} from "../../../utils/constants";
import { ActionType, UserInfo } from "../../../utils/helpers/types";
import { AuthTitle, WrapperThemeProvider } from "../AuthWithCognito";
import "./auth-with-oidc.scss";
import { Button } from "@aws-amplify/ui-react";

const AuthWithOidc: React.FC = () => {
  return (
    <WrapperThemeProvider>
      <AuthProvider
        {...{
          userStore: new WebStorageStateStore({ store: window.localStorage }),
          scope: "openid email profile",
          automaticSilentRenew: true,
          authority: OIDC.ISSUER,
          client_id: OIDC.CLIENT_ID,
          redirect_uri: OIDC.URL_REDIRECT || window.location.origin,
          responseType: "id_token",
          onSigninCallback: () => {
            window.history.replaceState(
              {},
              document.title,
              window.location.pathname
            );
          },
        }}
      >
        <AppWrapper />
      </AuthProvider>
    </WrapperThemeProvider>
  );
};

export default AuthWithOidc;

const AppWrapper: React.FC = () => {
  const auth = useAuth();
  console.log({
    isLoading: auth.isLoading,
    isAuthenticated: auth.isAuthenticated,
    activeNavigator: auth.activeNavigator,
    user: auth?.user,
    userProfile: auth?.user?.profile,
    auth,
  });

  const dispatch = useDispatch();

  useEffect(() => {
    if (!auth.user) return;

    if (AUTH_WITH_OIDC) {
      try {
        const { access_token, id_token, refresh_token, expires_at, profile } =
          auth.user;
        if (
          access_token &&
          id_token &&
          refresh_token &&
          expires_at &&
          profile
        ) {
          const loginUser: UserInfo = {
            userId: profile.sub,
            displayName:
              profile.name || (profile.unique_name as string) || "N/A",
            loginExpiration: expires_at || 0,
            isLogin: true,
            username: profile.name || "username unavailable",
          };
          localStorage.setItem(LOCAL_STORAGE_KEYS.accessToken, access_token);
          localStorage.setItem(LOCAL_STORAGE_KEYS.idToken, id_token);
          localStorage.setItem(LOCAL_STORAGE_KEYS.refreshToken, refresh_token);
          dispatch({ type: ActionType.UpdateUserInfo, state: loginUser });
        }
      } catch (error) {
        console.error("Initiating OIDC user state error: ", error);
      }
    }
  }, [dispatch, auth]);

  if (!auth.isAuthenticated || auth.error)
    return (
      <WrapperOidcLogin>
        {!auth.error ? null : (
          <div className="oidc-login-div-children-auth-error">
            Oops... Authentication error: <u>{auth.error.message}</u>
          </div>
        )}
        <Button
          // color="orange"
          colorTheme="overlay"
          variation="primary"
          width="300px"
          borderRadius="12px"
          isLoading={auth.isLoading}
          loadingText="Signing in..."
          onClick={() => void auth.signinRedirect()}
        >
          Click to sign in with OIDC IdP
        </Button>
      </WrapperOidcLogin>
    );

  // Authenticated
  return <App />;
};

function WrapperOidcLogin({ children }: { children: React.ReactNode }) {
  return (
    <div className="oidc-login-container">
      <AuthTitle />
      <div className="oidc-login-div">
        <h2>Please Sign In</h2>
        <div className="oidc-login-div-children">{children}</div>
        <div>
          <small>
            Authorized with OIDC{" "}
            <a
              target="_blank"
              href="https://github.com/authts/oidc-client-ts/blob/main/docs/protocols/authorization-code-grant-with-pkce.md"
            >
              PKCE Workflow
            </a>
          </small>
        </div>
      </div>
    </div>
  );
}
