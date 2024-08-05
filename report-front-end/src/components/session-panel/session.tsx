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

/*  const onItemClick = (event: any) => {
    if (event.detail.id === "delete") {
      // todo: call API to delete one session
      props.setSessions((current) => {
        return current.slice(0, props.index).concat(current.slice(props.index + 1));
      });
      props.setCurrSession(Math.max(props.currSession - 1, 0));
    }
  };*/

  const handleContextMenu = (event: any) => {
    // event.preventDefault();
    console.log("Right clicked");
    console.log({ x: event.pageX, y: event.pageY });
  };

  return (
    <div
      style={{ backgroundColor: props.index === props.currSession ? "lightgray" : "white" }}
      className="session_container">
      <div
        onContextMenu={handleContextMenu}>
        <Button
          iconName="contact"
          className="session"
          onClick={onClick}>
          {props.session.session_id}
        </Button>
      </div>
{/*      <div className="menu">
        <ButtonDropdown
          items={[
            { id: "delete", text: "Delete" },
          ]}
          variant="icon"
          onItemClick={onItemClick}
        />
      </div>*/}
    </div>
  );
};