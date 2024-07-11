import { useEffect, useState } from "react";
import { defaultDarkModeOverride, ThemeProvider } from "@aws-amplify/ui-react";
import App from "../../app";
import { Amplify } from "aws-amplify";
import { Storage } from "../../common/helpers/storage";
import { Mode } from "@cloudscape-design/global-styles";
import "@aws-amplify/ui-react/styles.css";
import { awsConfig } from "./aws-config";

export default function AppConfigured() {
  const [theme, setTheme] = useState(Storage.getTheme());

  useEffect(() => {
    (async () => {
      try {
        Amplify.configure(awsConfig);
      } catch (e) {
        console.error(e);
      }
    })();
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
              "--app-color-scheme",
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
      <App />
    </ThemeProvider>
  );
}
