import { AppLayout } from "@cloudscape-design/components";
import Navigation from "../navigation";
import {
  Dispatch,
  JSXElementConstructor,
  ReactElement,
  ReactNode,
  ReactPortal,
  SetStateAction,
} from "react";
import ConfigPanel from "../config-panel";

const PageLayout = (props: {
  content:
    | string
    | number
    | boolean
    | ReactElement<any, string | JSXElementConstructor<any>>
    | Iterable<ReactNode>
    | ReactPortal
    | null
    | undefined;
  toolsHide: boolean;
  setToolsHide: Dispatch<SetStateAction<boolean>>;
}) => {
  // const [openTools, setOpenTools] = useState(true);
  return (
    <AppLayout
      navigation={<Navigation />}
      navigationHide={true}
      content={props.content}
      tools={<ConfigPanel />}
      toolsOpen={true}
      onToolsChange={({ detail }) => {
        props.setToolsHide(true);
      }}
      toolsWidth={450}
      toolsHide={props.toolsHide}
    />
  );
};

export default PageLayout;
