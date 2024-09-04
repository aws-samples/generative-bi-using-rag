import {
  ButtonDropdownProps,
  TopNavigation,
} from "@cloudscape-design/components";
// import { Mode } from '@cloudscape-design/global-styles'
import { Density } from "@cloudscape-design/global-styles";
import { Auth } from "aws-amplify";
import { useState } from "react";
import { useSelector } from "react-redux";
import {
  APP_LOGO,
  APP_RIGHT_LOGO,
  APP_TITLE,
  CHATBOT_NAME,
  isLoginWithCognito,
} from "../../common/constant/constants";
import { Storage } from "../../common/helpers/storage";
import { UserState } from "../../common/helpers/types";
import "./style.scss";

export default function CustomTopNavigation() {
  // const [theme, setTheme] = useState<Mode>(Storage.getTheme())

  const userState = useSelector<UserState>((state) => state) as UserState;

  const onUserProfileClick = ({
    detail,
  }: {
    detail: ButtonDropdownProps.ItemClickDetails;
  }) => {
    if (detail.id === "signout") {
      if (isLoginWithCognito) {
        Auth.signOut().then();
      }
    }
  };

  const [isCompact, setIsCompact] = useState<boolean>(
    Storage.getDensity() === Density.Compact
  );

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
          title: APP_TITLE,
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
            text: userState?.userInfo?.displayName || "Authenticating",
            iconName: "user-profile",
            onItemClick: onUserProfileClick,
            items: [
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
