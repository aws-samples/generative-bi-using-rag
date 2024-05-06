import {
  ContentLayout,
  SpaceBetween,
  Header,
  Button,
  Alert,
  Container,
  CodeEditor,
  Link,
} from "@cloudscape-design/components";
import React, { useEffect, useState } from "react";
import "ace-builds/css/ace.css";
import "ace-builds/css/theme/dawn.css";
import "ace-builds/css/theme/tomorrow_night_bright.css";

const i18nStrings = {
  loadingState: "Loading code editor",
  errorState: "There was an error loading the code editor.",
  errorStateRecovery: "Retry",

  editorGroupAriaLabel: "Code editor",
  statusBarGroupAriaLabel: "Status bar",

  cursorPosition: (row: any, column: any) => `Ln ${row}, Col ${column}`,
  errorsTab: "Errors",
  warningsTab: "Warnings",
  preferencesButtonAriaLabel: "Preferences",

  paneCloseButtonAriaLabel: "Close",

  preferencesModalHeader: "Preferences",
  preferencesModalCancel: "Cancel",
  preferencesModalConfirm: "Confirm",
  preferencesModalWrapLines: "Wrap lines",
  preferencesModalTheme: "Theme",
  preferencesModalLightThemes: "Light themes",
  preferencesModalDarkThemes: "Dark themes",
};

const DefaultPage = () => {
  const [preferences, setPreferences] = useState(undefined as any);
  const [loading, setLoading] = useState(false);
  const [ace, setAce] = useState(undefined as any);

  useEffect(() => {
    async function loadAce() {
      const ace = await import("ace-builds");
      await import("ace-builds/webpack-resolver");
      ace.config.set("useStrictCSP", true);

      return ace;
    }

    loadAce()
      .then((ace) => setAce(ace))
      .finally(() => setLoading(false));
  }, []);
  return (
    <ContentLayout
      header={
        <SpaceBetween size="m">
          <Header
            variant="h1"
            info={<Link>Info</Link>}
            description="This is a generic description used in the header."
            actions={<Button variant="primary">Button</Button>}
          >
            How to send request
          </Header>

          <Alert statusIconAriaLabel="Info">This is a generic alert.</Alert>
        </SpaceBetween>
      }
    >
      <SpaceBetween size="m">
        <Container
          header={
            <Header variant="h2" description="Container description">
              How to send request
            </Header>
          }
        >
          Container content
        </Container>
        <CodeEditor
          ace={ace}
          language="javascript"
          value='
					import { get } from "../../tools/apiRequest"; 

					const getData = async () => {
						const respone = await get("https://aws.amazon.com/cn/");
						const resultJson = await respone.json();
						console.log("resultJson", resultJson);
					};'
          preferences={preferences}
          onPreferencesChange={(e) => setPreferences(e.detail)}
          loading={loading}
          i18nStrings={i18nStrings}
        />
      </SpaceBetween>
    </ContentLayout>
  );
};

export default DefaultPage;
