import React from "react";
import { TopNavigation } from "@cloudscape-design/components";

const CustomTopNavigation = () => {
  return (
    <TopNavigation
      identity={{
        href: "#",
        title: "GenBI App",
        logo: {
          src: "/Amazoncom-yellow-arrow.png",
          alt: "GenBI App",
        },
      }}
    />
  );
};

export default CustomTopNavigation;
