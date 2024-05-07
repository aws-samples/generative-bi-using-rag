import React, { useEffect } from "react";
import "./App.css";
import "@cloudscape-design/global-styles/index.css";
import { TopNavigation } from "@cloudscape-design/components";
import PageRouter from "./components/page-router";
import AlertMsg from "./components/alert-msg";
import { ActionType, UserState } from "./types/StoreTypes";
import { useSelector, useDispatch } from "react-redux";
import LoginPage from "./components/login-page";

function App() {
  const userInfo = useSelector<UserState>((state) => state) as UserState;
  const dispatch = useDispatch();
  console.log("userInfo", userInfo);
  useEffect(() => {
    checkLoginStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const checkLoginStatus = () => {
    if (userInfo.loginExpiration < +new Date()) {
      dispatch({ type: ActionType.Delete });
    }
  };
  return (
    <div className="Rp-Demo-App">
      <AlertMsg />
      {(!userInfo || !userInfo.userId || userInfo.userId === "") && (
        <LoginPage />
      )}
      {userInfo && userInfo.userId && userInfo.userId !== "" && (
        <>
          <TopNavigation
            identity={{
              href: "#",
              title: "GenBI App",
              logo: {
                src: "/Amazoncom-yellow-arrow.png",
                alt: "GenBI App",
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
        </>
      )}
    </div>
  );
}

export default App;
