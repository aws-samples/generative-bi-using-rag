import React from "react";
import { TopNavigation } from "@cloudscape-design/components";

const CustomTopNavigation = () => {
  return (
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
  );
};

export default CustomTopNavigation;
