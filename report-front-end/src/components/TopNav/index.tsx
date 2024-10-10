import { TopNavigation } from "@cloudscape-design/components";
// import { Mode } from '@cloudscape-design/global-styles'
import { useMsal } from "@azure/msal-react";
import { Density } from "@cloudscape-design/global-styles";
import { Auth } from "aws-amplify";
import { useState } from "react";
import { useAuth } from "react-oidc-context";
import { useSelector } from "react-redux";
import {
  APP_LOGO,
  APP_RIGHT_LOGO,
  APP_TITLE,
  APP_VERSION,
  AUTH_WITH_AZUREAD,
  AUTH_WITH_COGNITO,
  AUTH_WITH_OIDC,
  AUTH_WITH_SSO,
  CHATBOT_NAME,
} from "../../utils/constants";
import { Storage } from "../../utils/helpers/storage";
import { UserState } from "../../utils/helpers/types";
import "./style.scss";
export default function TopNav() {
  // const [theme, setTheme] = useState<Mode>(Storage.getTheme())
  const userInfo = useSelector((state: UserState) => state.userInfo);

  const [isCompact, setIsCompact] = useState<boolean>(
    Storage.getDensity() === Density.Compact
  );
  const { instance } = useMsal();
  const auth = useAuth();

  // const onChangeThemeClick = () => {
  //   if (theme === Mode.Dark) {
  //     setTheme(Storage.applyTheme(Mode.Light))
  //   } else {
  //     setTheme(Storage.applyTheme(Mode.Dark))
  //   }
  // }

  return (
    <div
      style={{ zIndex: 1002, top: 0, left: 0, right: 0, position: "fixed" }}
      id="awsui-top-navigation"
    >
      {APP_RIGHT_LOGO && (
        <img className="logo" src={APP_RIGHT_LOGO} alt="logo" />
      )}
      <TopNavigation
        identity={{
          href: "/",
          title: `${APP_TITLE} ${APP_VERSION}`,
          logo: APP_LOGO
            ? {
                src: APP_LOGO,
                alt: { CHATBOT_NAME } + " Logo",
              }
            : undefined,
        }}
        utilities={[
          // {
          //   type: 'button',
          //   text: theme === Mode.Dark ? 'Light Mode' : 'Dark Mode',
          //   onClick: onChangeThemeClick,
          // },
          {
            type: "button",
            iconName: isCompact ? "view-full" : "zoom-to-fit",
            text: isCompact ? "Compact" : "Comfortable",
            ariaLabel: "SpacingSwitch",
            onClick: () => {
              setIsCompact((prev) => {
                Storage.applyDensity(
                  !prev ? Density.Compact : Density.Comfortable
                );
                return !prev;
              });
            },
          },
          {
            type: "menu-dropdown",
            text: userInfo?.displayName || "Authenticating",
            // description: `username: ${userInfo?.username}`,
            iconName: "user-profile",
            onItemClick: ({ detail }) => {
              if (detail.id === "signout") {
                if (AUTH_WITH_COGNITO || AUTH_WITH_SSO) {
                  Auth.signOut();
                }
                if (AUTH_WITH_OIDC) {
                  auth.signoutSilent();
                }
                if (AUTH_WITH_AZUREAD) {
                  instance.logoutRedirect({
                    postLogoutRedirectUri: "/",
                  });
                }
              }
            },
            items: [
              {
                itemType: "group",
                id: "user-info",
                text: "User Information",
                items: [
                  {
                    id: "0",
                    text: `username: ${userInfo?.username}`,
                  },
                  {
                    id: "1",
                    text: `userId: ${userInfo?.userId}`,
                  },
                  {
                    id: "2",
                    text: `loginExpiration: ${userInfo?.loginExpiration}`,
                    disabled: true,
                  },
                ],
              },
              {
                id: "signout",
                text: "Sign out",
              },
            ],
          },
        ]}
      />
    </div>
  );
}
