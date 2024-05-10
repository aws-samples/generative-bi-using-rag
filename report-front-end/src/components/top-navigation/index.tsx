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
      utilities={[
        {
          type: "menu-dropdown",
          text: "Customer Name",
          description: "aws_example@amazon.com",
          iconName: "user-profile",
          items: [
            { id: "signout", text: "Sign out" },
          ],
        },
      ]}
    />
  );
};

export default CustomTopNavigation;
