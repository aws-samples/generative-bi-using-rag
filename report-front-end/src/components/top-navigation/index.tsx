import { TopNavigation } from "@cloudscape-design/components";
// import { Mode } from '@cloudscape-design/global-styles'
import { Density } from "@cloudscape-design/global-styles";
import { useState } from "react";
import { APP_LOGO, APP_RIGHT_LOGO, APP_TITLE, CHATBOT_NAME } from "../../common/constant/constants";
import { Storage } from "../../common/helpers/storage";
import "./style.scss";

export default function CustomTopNavigation() {

  // const onChangeThemeClick = () => {
  //   if (theme === Mode.Dark) {
  //     setTheme(Storage.applyTheme(Mode.Light))
  //   } else {
  //     setTheme(Storage.applyTheme(Mode.Dark))
  //   }
  // }

  const [isCompact, setIsCompact] = useState<boolean>(
    Storage.getDensity() === Density.Compact
  );

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
          }
        ]}
      />
    </div>
  );
}
