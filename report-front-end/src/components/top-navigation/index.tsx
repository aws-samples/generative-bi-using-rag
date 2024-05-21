import React from "react";
import { TopNavigation } from "@cloudscape-design/components";
import "./style.scss"

const CustomTopNavigation = () => {
  return (
    <div className="top-nav" id="awsui-top-navigation">
      <TopNavigation
        identity={{
          href: "#",
          title: "Guidance for Generative BI on Amazon Web Services",
          logo: {
            src: "/Amazoncom-yellow-arrow.png",
            alt: "amazon icon",
          },
        }}
      />
    </div>
  );
};

export default CustomTopNavigation;
