import { AppLayout } from "@cloudscape-design/components";
import Navigation from "../navigation";
import {
  ReactElement,
  JSXElementConstructor,
  ReactNode,
  ReactPortal,
  useState,
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
}) => {
  const [openTools, setOpenTools] = useState(true);
  return (
    <AppLayout
      navigation={<Navigation />}
      content={props.content}
      tools={<ConfigPanel />}
      toolsOpen={openTools}
      onToolsChange={({ detail }) => {
        setOpenTools(detail.open);
      }}
    />
  );
};

export default PageLayout;
