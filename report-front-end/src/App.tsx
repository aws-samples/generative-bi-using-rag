import React from "react";
import "./App.css";
import "@cloudscape-design/global-styles/index.css";
import { TopNavigation } from "@cloudscape-design/components";
import PageRouter from "./componments/page-router";
import AlertMsg from "./componments/alert-msg";

function App() {
  return (
    <div className="Rp-Demo-App">
      <AlertMsg />
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
    </div>
  );
}

export default App;
