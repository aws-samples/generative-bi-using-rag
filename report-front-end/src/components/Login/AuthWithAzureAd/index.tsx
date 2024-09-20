import { Button } from "@aws-amplify/ui-react";
import { PublicClientApplication } from "@azure/msal-browser";
import { MsalProvider, useIsAuthenticated, useMsal } from "@azure/msal-react";
import React, { useEffect } from "react";
import { useDispatch } from "react-redux";
import App from "../../../app";
import {
  AUTH_WITH_AZUREAD,
  LOCAL_STORAGE_KEYS,
} from "../../../utils/constants";
import { ActionType, UserInfo } from "../../../utils/helpers/types";
import { AuthTitle, WrapperThemeProvider } from "../AuthWithCognito";
import "./auth-with-oidc.scss";
import { loginRequest, msalConfig } from "./authConfig";

const msalInstance = new PublicClientApplication(msalConfig);

const AuthWithAzureAd: React.FC = () => {
  return (
    <WrapperThemeProvider>
      <MsalProvider instance={msalInstance}>
        <AppWrapper />
      </MsalProvider>
    </WrapperThemeProvider>
  );
};

export default AuthWithAzureAd;

const AppWrapper: React.FC = () => {
  const isAuthenticated = useIsAuthenticated();
  const { inProgress } = useMsal();
  console.log({ inProgress });
  if (!isAuthenticated) {
    return (
      <WrapperOidcLogin>
        <Button
          // color="orange"
          colorTheme="overlay"
          variation="primary"
          width="350px"
          borderRadius="12px"
          isLoading={inProgress !== "none"}
          loadingText={`Processing Status: ${inProgress}`}
          onClick={() => {
            msalInstance.loginRedirect(loginRequest).catch((e) => {
              console.log(e);
            });

            // if (loginType === "popup") {
            //   instance.loginPopup(loginRequest).catch((e) => {
            //     console.log(e);
            //   });
            // }
          }}
        >
          Click to authenticate with AzureAD
        </Button>
      </WrapperOidcLogin>
    );
  }
  return <AppContainer />;
};

function AppContainer() {
  const {
    instance,
    accounts: [account],
  } = useMsal();

  const dispatch = useDispatch();

  useEffect(() => {
    if (!account || !instance) return;

    if (AUTH_WITH_AZUREAD) {
      try {
        instance
          .acquireTokenSilent({ scopes: ["User.Read"], account })
          .then((accountDetails) => {
            console.log({ "AzureAD Account Details": accountDetails });
            // window.accountDetails = accountDetails;
            const { accessToken, idToken, uniqueId } = accountDetails;
            const { username, name } = account;
            if (accessToken && idToken && username && name && uniqueId) {
              const loginUser: UserInfo = {
                userId: uniqueId,
                displayName: name || username || "N/A",
                loginExpiration: 0,
                isLogin: true,
                username: username || "username unavailable",
              };
              localStorage.setItem(LOCAL_STORAGE_KEYS.accessToken, accessToken);
              localStorage.setItem(LOCAL_STORAGE_KEYS.idToken, idToken);
              localStorage.setItem(LOCAL_STORAGE_KEYS.refreshToken, "");
              dispatch({ type: ActionType.UpdateUserInfo, state: loginUser });
            } else {
              const msg = "Something is missing during authentication";
              console.warn({
                [msg]: {
                  accessToken,
                  idToken,
                  username,
                  name,
                  uniqueId,
                },
              });
              throw new Error(msg);
            }
          });
      } catch (error) {
        console.error("Initiating AzureAD user state error: ", error);
      }
    }
  }, [dispatch, account, instance]);
  return <App />;
}

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
