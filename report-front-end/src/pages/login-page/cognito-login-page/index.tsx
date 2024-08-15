import {
  Authenticator,
  defaultDarkModeOverride,
  Image,
  ThemeProvider,
  View,
} from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import { Mode } from "@cloudscape-design/global-styles";
import { Amplify } from "aws-amplify";
import { useEffect, useState } from "react";
import App from "../../../app";
import {
  APP_LOGO,
  APP_LOGO_DISPLAY_ON_LOGIN_PAGE,
  isLoginWithCognito,
} from "../../../common/constant/constants";
import { Storage } from "../../../common/helpers/storage";
import { awsConfig } from "./aws-config";

export default function AppConfigured() {
  const [theme, setTheme] = useState(Storage.getTheme());

  useEffect(() => {
    if (isLoginWithCognito) {
      console.log("Cognito configured");
      (async () => {
        try {
          Amplify.configure(awsConfig);
        } catch (e) {
          console.error(e);
        }
      })();
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
        components={{
          Header() {
            return APP_LOGO && APP_LOGO_DISPLAY_ON_LOGIN_PAGE ? (
              <View textAlign="center" marginTop="-120px">
                <Image
                  alt="App logo"
                  // src="https://docs.amplify.aws/assets/logo-dark.svg"
                  src={APP_LOGO}
                  height="120px"
                />
              </View>
            ) : null;
          },
        }}
      >
        {({ signOut, user }) => <App signOut={signOut} user={user as any} />}
      </Authenticator>
    </ThemeProvider>
  );
}
