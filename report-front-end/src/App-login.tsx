import React, { useEffect, useState } from "react";
import "./App.css";
import "@cloudscape-design/global-styles/index.css";
import { Spinner, TopNavigation } from "@cloudscape-design/components";
import PageRouter from "./components/page-router";
import AlertMsg from "./components/alert-msg";
import { Amplify } from "aws-amplify";
import { Authenticator, Heading, useTheme } from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import Axios from "axios";
import { AmplifyConfigType } from "./types/AmplifyType";
import { AMPLIFY_CONFIG_JSON } from "./tools/const";

const components = {
  SignIn: {
    Header() {
      const { tokens } = useTheme();

      return (
        <Heading
          padding={`${tokens.space.xl} 0 0 ${tokens.space.xl}`}
          level={3}
        >
          Sign in to your account
        </Heading>
      );
    },
  },
};

const SignInRouter: React.FC = () => {
  return (
    <>
      <Authenticator hideSignUp components={components}>
        {({ signOut, user }) => {
          return (
            <>
              <TopNavigation
                identity={{
                  href: "#",
                  title: "Demo App",
                  logo: {
                    src: "/logo-small-top-navigation.svg",
                    alt: "Demo App",
                  },
                }}
                utilities={[
                  {
                    type: "button",
                    text: "Link",
                    href: "https://aws.amazon.com/cn/",
                    external: true,
                    externalIconAriaLabel: " (opens in a new tab)",
                  },
                  {
                    type: "button",
                    iconName: "notification",
                    title: "Notifications",
                    ariaLabel: "Notifications (unread)",
                    badge: true,
                    disableUtilityCollapse: false,
                  },
                  {
                    type: "menu-dropdown",
                    iconName: "settings",
                    ariaLabel: "Settings",
                    title: "Settings",
                    items: [
                      {
                        id: "settings-org",
                        text: "Organizational settings",
                      },
                      {
                        id: "settings-project",
                        text: "Project settings",
                      },
                    ],
                  },
                  {
                    type: "menu-dropdown",
                    text: "Customer Name",
                    description: "aws_example@amazon.com",
                    iconName: "user-profile",
                    onItemClick: (e) => {
                      console.log("e", e);
                    },
                    items: [
                      { id: "profile", text: "Profile" },
                      { id: "preferences", text: "Preferences" },
                      { id: "security", text: "Security" },
                      {
                        id: "support-group",
                        text: "Support",
                        items: [
                          {
                            id: "documentation",
                            text: "Documentation",
                            href: "#",
                            external: true,
                            externalIconAriaLabel: " (opens in new tab)",
                          },
                          { id: "support", text: "Support" },
                          {
                            id: "feedback",
                            text: "Feedback",
                            href: "#",
                            external: true,
                            externalIconAriaLabel: " (opens in new tab)",
                          },
                        ],
                      },
                      { id: "signout", text: "Sign out" },
                    ],
                  },
                ]}
              />
              <PageRouter />
            </>
          );
        }}
      </Authenticator>
    </>
  );
};

function App() {
  const [loadingConfig, setLoadingConfig] = useState(true);

  useEffect(() => {
    const timeStamp = new Date().getTime();
    // [Optional] Add monitoring
    // const resMonitroing = Axios.get(
    //   `/aws-monitoring-exports.json?timestamp=${timeStamp}`
    // );
    const recConsole = Axios.get(`/aws-exports.json?timestamp=${timeStamp}`);
    // Axios.all([resMonitroing, recConsole]).then(
    Axios.all([recConsole]).then(
      Axios.spread((recConsole) => {
        const res: AmplifyConfigType = recConsole.data;
        // res.aws_monitoring_api_key = resMonitroing.data.aws_monitoring_api_key;
        // res.aws_monitoring_url = resMonitroing.data.aws_monitoring_url;
        // res.aws_monitoring_stack_name =
        //   resMonitroing.data.aws_monitoring_stack_name;
        const configData: AmplifyConfigType = res;

        localStorage.setItem(AMPLIFY_CONFIG_JSON, JSON.stringify(res));
        Amplify.configure(configData);
        setLoadingConfig(false);
      })
    );
  }, []);
  return (
    <div className="Rp-Demo-App">
      <AlertMsg />
      {loadingConfig ? <Spinner size="large" /> : <SignInRouter />}
    </div>
  );
}

export default App;
