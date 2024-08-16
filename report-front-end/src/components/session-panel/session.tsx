import { Button } from "@cloudscape-design/components";
import "./style.scss";
import { Dispatch, SetStateAction } from "react";
import { Session } from "./types";

export const SessionPanel = (props: {
  session: Session,
  index: number,
  currSessionId: string,
  setCurrSessionId: Dispatch<SetStateAction<string>>,
  setSessions: Dispatch<SetStateAction<Session[]>>,
}) => {

  const onClick = () => {
    console.log("Switch sessionId: ", props.session);
    props.setCurrSessionId(props.session.session_id);
  };

  return (
    <div
      style={{ backgroundColor: props.session.session_id === props.currSessionId ? "lightgray" : "white" }}
      className="session_container">
      <Button
        iconName="contact"
        className="session"
        onClick={onClick}>
        {props.session.messages.length > 0 ? props.session.messages[0].content as string : "New Chat"}
      </Button>
    </div>
  );
};