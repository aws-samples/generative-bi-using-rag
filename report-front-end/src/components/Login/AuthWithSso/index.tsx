import {
  Authenticator,
  Button,
  Divider,
  Heading,
  View,
} from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import { Amplify, Auth } from "aws-amplify";
import { useEffect, useState } from "react";
import { SSO_FED_AUTH_PROVIDER } from "../../../utils/constants";
import {
  AppWrapper,
  AuthTitle,
  WrapperThemeProvider,
} from "../AuthWithCognito";
import "../AuthWithCognito/layout-with-cognito.css";
import { awsConfig } from "./aws-config";

/**
 * Authenticate the app with Single-sign-on
 * @WARNING: this method is only for amazon cognito OIDC single-sign-on
 */
export default function AuthWithSso() {
  const [isLoading, setIsLoading] = useState(false);
  useEffect(() => {
    console.log("Cognito with SSO configured");
    try {
      // extra configs for SSO
      Amplify.configure(awsConfig);
    } catch (e) {
      console.error(e);
    }
  }, []);

  return (
    <WrapperThemeProvider>
      <Authenticator
        signUpAttributes={["email"]}
        hideSignUp
        components={{
          Header: AuthTitle,
          SignIn: {
            Header() {
              return (
                <View
                  padding="0.3rem 2rem"
                  style={{ borderTop: "2px solid black" }}
                >
                  <Heading
                    fontSize="20px"
                    padding="1rem 0"
                    fontWeight={400}
                    textAlign="center"
                  >
                    Please Sign In
                  </Heading>
                  <Button
                    colorTheme="overlay"
                    // variation="primary"
                    loadingText="Signing in..."
                    isLoading={isLoading}
                    disabled={isLoading}
                    width="100%"
                    onClick={async () => {
                      try {
                        setIsLoading(true);
                        await Auth.federatedSignIn({
                          customProvider: SSO_FED_AUTH_PROVIDER,
                        });
                      } catch (error) {
                        console.error(error);
                      }
                    }}
                  >
                    Click to sign in with SSO
                  </Button>
                  <Divider
                    orientation="horizontal"
                    label="or"
                    margin="2rem 0 0 0"
                  />
                </View>
              );
            },
          },
        }}
      >
        {({ signOut, user }) => (
          <AppWrapper signOut={signOut} user={user as any} />
        )}
      </Authenticator>
    </WrapperThemeProvider>
  );
}
