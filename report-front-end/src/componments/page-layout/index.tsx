import { AppLayout } from "@cloudscape-design/components";
import Navigation from "../navigation";
import {
  ReactElement,
  JSXElementConstructor,
  ReactNode,
  ReactPortal,
} from "react";

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
  return <AppLayout navigation={<Navigation />} content={props.content} />;
};

export default PageLayout;
