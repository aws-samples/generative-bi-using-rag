import { SessionPanel } from "./session";
import { Box, Button } from "@cloudscape-design/components";
import "./style.scss";
import { Dispatch, SetStateAction, useEffect } from "react";
import { Session } from "./types";
import { v4 as uuid } from "uuid";
import { getSessions } from "../../common/api/API";
import { UserState } from "../../common/helpers/types";
import { useSelector } from "react-redux";

export const Sessions = (
  props: {
    sessions: Session[];
    setSessions: Dispatch<SetStateAction<Session[]>>;
    currentSessionId: string;
    setCurrentSessionId: Dispatch<SetStateAction<string>>;
  },
) => {

  const userInfo = useSelector<UserState>((state) => state) as UserState;

  useEffect(() => {
    const sessionItem = {
      user_id: userInfo.userInfo.userId,
      profile_name: userInfo.queryConfig.selectedDataPro,
    };
    getSessions(sessionItem).then(
      response => {
        console.log("Sessions: ", response);
        const sessionId = uuid();
        props.setSessions([
          {
            session_id: sessionId,
            title: "New Chat",
            messages: []
          }, ...(response.filter((item: any) => item.session_id !== "")
            .map((item: any) => {
                return {
                  session_id: item.session_id,
                  title: item.title,
                  messages: []
                };
              },
            ))]);
        props.setCurrentSessionId(sessionId);
      });
  }, [userInfo.queryConfig.selectedDataPro]);

  const addNewSession = () => {
    const sessionId = uuid();
    props.setSessions([
      {
        session_id: sessionId,
        title: "New Chat",
        messages: [],
      }, ...props.sessions]);
    props.setCurrentSessionId(sessionId);
  };

  return (
    <Box margin={{ top: "l" }}>
      <Button
        fullWidth
        iconName="add-plus"
        className="new_session_btn"
        onClick={addNewSession}>
        New Chat
      </Button>
      <div style={{ marginTop: 20 }}>
        {props.sessions
          .map((session, idx: number) => (
            <SessionPanel
              key={idx}
              index={idx}
              currSessionId={props.currentSessionId}
              setCurrSessionId={props.setCurrentSessionId}
              session={session}
              setSessions={props.setSessions}
            />
          ))}
      </div>
    </Box>
  );
};