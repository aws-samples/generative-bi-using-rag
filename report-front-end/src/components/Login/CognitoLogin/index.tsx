import {
  Authenticator,
  Button,
  defaultDarkModeOverride,
  Divider,
  Heading,
  Image,
  ThemeProvider,
  useTheme,
  View,
} from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import { Mode } from "@cloudscape-design/global-styles";
import { Amplify, Auth } from "aws-amplify";
import { useEffect, useState } from "react";
import App from "../../../app";
import {
  APP_LOGO,
  APP_LOGO_DISPLAY_ON_LOGIN_PAGE,
  APP_TITLE,
  APP_VERSION,
  SSO_FED_AUTH_PROVIDER,
  useSSOLogin,
} from "../../../utils/constants";
import { Storage } from "../../../utils/helpers/storage";
import { awsConfig } from "./aws-config";
import "./layout-with-cognito.css";

export default function CognitoLogin() {
  const [theme, setTheme] = useState(Storage.getTheme());

  useEffect(() => {
    console.log("Cognito configured");
    try {
      Amplify.configure(awsConfig);
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (
          mutation.type === "attributes" &&
          mutation.attributeName === "style"
        ) {
          const newValue =
            document.documentElement.style.getPropertyValue(
              "--app-color-scheme"
            );

          const mode = newValue === "dark" ? Mode.Dark : Mode.Light;
          if (mode !== theme) {
            setTheme(mode);
          }
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["style"],
    });

    return () => {
      observer.disconnect();
    };
  }, [theme]);

  const [isLoading, setIsLoading] = useState(false);

  return (
    <ThemeProvider
      theme={{
        name: "default-theme",
        overrides: [defaultDarkModeOverride],
      }}
      colorMode={theme === Mode.Dark ? "dark" : "light"}
    >
      <Authenticator
        signUpAttributes={["email"]}
        components={
          !useSSOLogin
            ? {
                Header() {
                  const { tokens } = useTheme();
                  return !APP_LOGO_DISPLAY_ON_LOGIN_PAGE ? (
                    <Title />
                  ) : (
                    <View textAlign="center" padding={tokens.space.xxl}>
                      {APP_LOGO ? (
                        <Image
                          alt="App logo"
                          src={APP_LOGO}
                          // src="https://docs.amplify.aws/assets/logo-dark.svg"
                        />
                      ) : (
                        <Heading padding={tokens.space.small} level={4}>
                          {APP_TITLE}
                        </Heading>
                      )}
                    </View>
                  );
                },
              }
            : {
                Header: Title,
                SignIn: {
                  Header() {
                    return (
                      <View width="87%" margin="1rem auto">
                        <Button
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
                          Sign In with SSO
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
              }
        }
      >
        {({ signOut, user }) => <App signOut={signOut} user={user as any} />}
      </Authenticator>
    </ThemeProvider>
  );
}

function Title() {
  const { tokens } = useTheme();
  return (
    <View
      textAlign="center"
      margin={`${tokens.space.large} auto`}
      position="relative"
    >
      <View padding={tokens.space.small}>
        <Heading fontWeight="400" level={3}>
          Generative Business Intelligence
        </Heading>
        {APP_VERSION && <Heading fontWeight="200">{APP_VERSION}</Heading>}
      </View>

      <Heading fontWeight="200">Guidance on Amazon Web Services</Heading>
      <Image
        width="50px"
        alt="Amazon Web Services Logo"
        src="/smile-logo.png"
      />
    </View>
  );
}
