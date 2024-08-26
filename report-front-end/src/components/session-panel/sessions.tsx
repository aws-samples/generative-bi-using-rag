import { Box, Button } from "@cloudscape-design/components";
import { useEffect } from "react";
import { useSelector } from "react-redux";
import { v4 as uuid } from "uuid";
import { getSessions } from "../../common/api/API";
import { UserState } from "../../common/helpers/types";
import { SessionPanel } from "./session";
import "./style.scss";
import useGlobalContext from "../../hooks/useGlobalContext";

export const Sessions = () => {
  const userInfo = useSelector((state: UserState) => state.userInfo);
  const queryConfig = useSelector((state: UserState) => state.queryConfig);
  const { setCurrentSessionId, setSessions, sessions, currentSessionId } =
    useGlobalContext();
  useEffect(() => {
    const sessionItem = {
      user_id: userInfo.userId,
      profile_name: queryConfig.selectedDataPro,
    };
    getSessions(sessionItem).then((response) => {
      console.log("Sessions: ", response);
      const sessionId = uuid();
      setSessions([
        {
          session_id: sessionId,
          title: "New Chat",
          messages: [],
        },
        ...response
          .filter((item: any) => item.session_id !== "")
          .map((item: any) => {
            return {
              session_id: item.session_id,
              title: item.title,
              messages: [],
            };
          }),
      ]);
      setCurrentSessionId(sessionId);
    });
  }, [
    queryConfig.selectedDataPro,
    setCurrentSessionId,
    setSessions,
    userInfo.userId,
  ]);

  return (
    <Box margin={{ top: "l" }}>
      <Button
        fullWidth
        iconName="add-plus"
        className="new_session_btn"
        onClick={() => {
          const sessionId = uuid();
          setSessions([
            {
              session_id: sessionId,
              title: "New Chat",
              messages: [],
            },
            ...sessions,
          ]);
          setCurrentSessionId(sessionId);
        }}
      >
        New Chat
      </Button>
      <div style={{ marginTop: 20 }}>
        {sessions.map((session, idx: number) => (
          <SessionPanel
            key={idx}
            index={idx}
            currSessionId={currentSessionId}
            setCurrSessionId={setCurrentSessionId}
            session={session}
            setSessions={setSessions}
          />
        ))}
      </div>
    </Box>
  );
};
