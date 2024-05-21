import { SideNavigation } from "@cloudscape-design/components";
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
      ]}
    />
  );
};

export default Navigation;
