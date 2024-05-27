import React from "react";
import { TopNavigation } from "@cloudscape-design/components";
import "./style.scss"
import { APP_LOGO, APP_RIGHT_LOGO, APP_TITLE } from "../../tools/const";

const CustomTopNavigation = () => {

  return (
    <div className="top-nav" id="awsui-top-navigation">
      {APP_RIGHT_LOGO && (
        <img className="logo" src={APP_RIGHT_LOGO} alt="logo"/>
      )
      }
      <TopNavigation
        identity={{
          href: "#",
          title: APP_TITLE,
          logo: {
            src: APP_LOGO,
            alt: "icon",
          },
        }}
      />
    </div>
  );
};

export default CustomTopNavigation;
