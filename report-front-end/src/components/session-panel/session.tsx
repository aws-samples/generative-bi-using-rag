import { Button } from "@cloudscape-design/components";
import "./style.scss";
import { Dispatch, SetStateAction } from "react";

export const SessionPanel = (props: {
  session: any,
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
        {props.session.session_id}
      </Button>
    </div>
  );
};