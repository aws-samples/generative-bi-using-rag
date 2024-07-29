import { AppLayout } from "@cloudscape-design/components";
import { useNavigationPanelState } from "../../common/hooks/use-navigation-panel-state";
import { Dispatch, ReactElement, ReactNode, ReactPortal, SetStateAction } from "react";

export default function BaseAppLayout(
  props: {
    content:
      | string
      | number
      | boolean
      | ReactElement
      | Iterable<ReactNode>
      | ReactPortal
      | null
      | undefined;
    info: ReactElement,
    navigation: ReactElement,
    toolsHide: boolean;
    setToolsHide: Dispatch<SetStateAction<boolean>>;
  }
) {
  const [navigationPanelState, setNavigationPanelState] =
    useNavigationPanelState();

  return (
    <AppLayout
      headerSelector="#awsui-top-navigation"
      content={props.content}
      navigation={props.navigation}
      navigationWidth={300}
      navigationHide={false}
      navigationOpen={!navigationPanelState.collapsed}
      onNavigationChange={({ detail }) =>
        setNavigationPanelState({ collapsed: !detail.open })
      }
      tools={props.info}
      toolsOpen={true}
      onToolsChange={({ detail }) => {
        props.setToolsHide(!detail.open);
      }}
      toolsWidth={450}
      toolsHide={props.toolsHide}
    />
  );
}
