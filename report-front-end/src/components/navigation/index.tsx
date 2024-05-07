import { Badge, SideNavigation } from "@cloudscape-design/components";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

const Navigation = () => {
  const navigate = useNavigate();

  const [activeHref, setActiveHref] = useState(window.location.pathname ?? "/");
  return (
    <SideNavigation
      activeHref={activeHref}
      header={{ href: "/", text: "GenBI" }}
      onFollow={(event) => {
        if (!event.detail.external) {
          event.preventDefault();
          setActiveHref(event.detail.href);
          navigate(event.detail.href);
        }
      }}
      items={[
        { type: "link", text: "Playground", href: "/" },
        { type: "divider" },
        { type: "link", text: "Page 1 (table)", href: "/page1" },
        { type: "link", text: "Page 2 (chart)", href: "/page2" },
        { type: "divider" },
        {
          type: "link",
          text: "Notifications",
          href: "#/notifications",
          info: <Badge color="red">23</Badge>,
        },
        {
          type: "link",
          text: "Documentation",
          href: "https://cloudscape.design/components/side-navigation/",
          external: true,
        },
      ]}
    />
  );
};

export default Navigation;
