import { SessionPanel } from "./session";
import { Box, Button } from "@cloudscape-design/components";
import "./style.scss";
import { Dispatch, SetStateAction, useEffect } from "react";
import { Session } from "./types";
import { v4 as uuid } from "uuid";
import { getSessions } from "../../common/api/API";
import { UserState } from "../../common/helpers/types";
import { useSelector } from "react-redux";

export const Sessions = (props: {
  sessions: Session[];
  setSessions: Dispatch<SetStateAction<Session[]>>;
  currentSession: number;
  setCurrentSession: Dispatch<SetStateAction<number>>;
}) => {
  const userInfo = useSelector<UserState>((state) => state) as UserState;

  useEffect(() => {
    const sessionItem = {
      user_id: userInfo.userInfo.userId,
      profile_name: userInfo.queryConfig.selectedDataPro,
    };
    getSessions(sessionItem).then((response) => {
      if (!response) return;
      console.log("sessions: ", response);
      props.setSessions([
        {
          session_id: uuid(),
          messages: [],
        },
        ...response,
      ]);
      props.setCurrentSession(0);
    });
  }, [userInfo.queryConfig.selectedDataPro]);

  const addNewSession = () => {
    props.setSessions([
      {
        session_id: uuid(),
        messages: [],
      },
      ...props.sessions,
    ]);
    props.setCurrentSession(0);
  };

  return (
    <Box margin={{ top: "l" }}>
      <Button
        fullWidth
        iconName="add-plus"
        className="new_session_btn"
        onClick={addNewSession}
      >
        New Chat
      </Button>
      <div style={{ marginTop: 20 }}>
        {props.sessions.map((session, idx: number) => (
          <SessionPanel
            key={idx}
            index={idx}
            currSession={props.currentSession}
            setCurrSession={props.setCurrentSession}
            session={session}
            setSessions={props.setSessions}
          />
        ))}
      </div>
    </Box>
  );
};
