import { Button } from "@cloudscape-design/components";
import "./style.scss";
import { Dispatch, SetStateAction } from "react";
import { Session } from "./types";

export const SessionPanel = (props: {
  session: Session,
  index: number,
  currSession: number,
  setCurrSession: Dispatch<SetStateAction<number>>,
  setSessions: Dispatch<SetStateAction<any[]>>,
}) => {

  const onClick = () => {
    props.setCurrSession(props.index);
  };

  return (
    <div
      style={{ backgroundColor: props.index === props.currSession ? "lightgray" : "white" }}
      className="session_container">
      <Button
        iconName="contact"
        className="session"
        onClick={onClick}>
        {props.session.messages.length > 0 ? props.session.title : "New Chat"}
      </Button>
    </div>
  );
};