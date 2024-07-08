import {
  ButtonDropdownProps,
  TopNavigation,
} from "@cloudscape-design/components";
// import { Mode } from '@cloudscape-design/global-styles'
import { Auth } from "aws-amplify";
import { useEffect, useState } from "react";
// import { Storage } from '../../common/helpers/storage'
import {
  APP_LOGO,
  APP_RIGHT_LOGO,
  APP_TITLE,
  CHATBOT_NAME,
} from "../../common/constant/constants";
import "./style.scss";

export default function CustomTopNavigation() {
  const [userName, setUserName] = useState<string>("Authenticating");
  const [userEmail, setUserEmail] = useState<string>("Authenticating");
  // const [theme, setTheme] = useState<Mode>(Storage.getTheme())

  useEffect(() => {
    async function getUser() {
      const result = await Auth.currentUserInfo();

      if (!result || Object.keys(result).length === 0) {
        await Auth.signOut();
        return;
      }

      setUserEmail(result?.attributes?.email || "Not logged in");
      setUserName(result?.username || "Not logged in");
    }
    getUser();
  }, []);

  // const onChangeThemeClick = () => {
  //   if (theme === Mode.Dark) {
  //     setTheme(Storage.applyTheme(Mode.Light))
  //   } else {
  //     setTheme(Storage.applyTheme(Mode.Dark))
  //   }
  // }

  const onUserProfileClick = ({
    detail,
  }: {
    detail: ButtonDropdownProps.ItemClickDetails;
  }) => {
    if (detail.id === "signout") {
      Auth.signOut().then();
    }
  };

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
            type: "menu-dropdown",
            text: userName,
            description: userEmail,
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
