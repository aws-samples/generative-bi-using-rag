import { AppLayout, AppLayoutProps } from "@cloudscape-design/components";
import { Dispatch, SetStateAction, useState } from "react";
import { Storage } from "../utils/helpers/storage";

export default function BaseAppLayout(props: {
  content: AppLayoutProps["content"];
  tools: AppLayoutProps["tools"];
  navigation: AppLayoutProps["navigation"];
  toolsHide: boolean;
  setToolsHide: Dispatch<SetStateAction<boolean>>;
}) {
  const [currentState, setCurrentState] = useState(
    Storage.getNavigationPanelState()
  );

  return (
    <AppLayout
      headerSelector="#awsui-top-navigation"
      content={props.content}
      navigation={props.navigation}
      tools={props.tools}
      toolsOpen
      toolsHide={props.toolsHide}
      onToolsChange={({ detail }) => {
        props.setToolsHide(!detail.open);
      }}
      toolsWidth={450}
      navigationWidth={300}
      navigationHide={false}
      navigationOpen={!currentState.collapsed}
      onNavigationChange={({ detail }) =>
        setCurrentState(
          Storage.setNavigationPanelState({ collapsed: !detail.open })
        )
      }
    />
  );
}
