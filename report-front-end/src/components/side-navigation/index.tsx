import { SideNavigation, } from "@cloudscape-design/components";
import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { CHATBOT_NAME } from "../../common/constant/constants";

export default function NavigationPanel() {
  const location = useLocation();
  const [activeHref, setActiveHref] = useState(location.pathname ?? "/playground");
  const navigate = useNavigate();
  const items: any = [];

  return (
    <SideNavigation
      activeHref={activeHref}
      onFollow={event => {
        if (!event.detail.external) {
          event.preventDefault();
          setActiveHref(event.detail.href);
          navigate(event.detail.href);
        }
      }}
      header={{ href: "/", text: CHATBOT_NAME }}
      items={items}
    />
  );
}
