import {
  Box,
  Button,
  ContentLayout,
  Header,
  Spinner,
} from "@cloudscape-design/components";
import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { v4 as uuid } from "uuid";
import { getSessions } from "../../utils/api/API";
import { UserState } from "../../utils/helpers/types";
import "./style.scss";
import useGlobalContext from "../../hooks/useGlobalContext";

export const PanelSideNav = () => {
  const userInfo = useSelector((state: UserState) => state.userInfo);
  const queryConfig = useSelector((state: UserState) => state.queryConfig);
  const { setCurrentSessionId, setSessions, sessions, currentSessionId } =
    useGlobalContext();
  const [loadingSessions, setLoadingSessions] = useState(false);

  useEffect(() => {
    setLoadingSessions(true);
    getSessions({
      user_id: userInfo.userId,
      profile_name: queryConfig.selectedDataPro,
    })
      .then((sessions) => {
        if (sessions?.length) {
          setCurrentSessionId(sessions[0].session_id);
          return setSessions(sessions);
        }
        const newSessionId = uuid();
        setSessions([
          {
            session_id: newSessionId,
            title: "New Chat",
            messages: [],
          },
        ]);
        setCurrentSessionId(newSessionId);
      })
      .finally(() => {
        setLoadingSessions(false);
      });
  }, [
    userInfo.userId,
    queryConfig.selectedDataPro,
    setCurrentSessionId,
    setSessions,
  ]);

  return (
    <ContentLayout
      defaultPadding
      disableOverlap
      headerVariant="divider"
      header={<Header variant="h3">{queryConfig.selectedDataPro}</Header>}
    >
      {loadingSessions ? (
        <Box variant="h4" margin="m" padding="m">
          <Spinner /> Loading sessions...
        </Box>
      ) : (
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
            {sessions?.map((ses, idx) => (
              <div
                key={idx}
                style={{
                  backgroundColor:
                    ses.session_id === currentSessionId ? "lightgray" : "white",
                }}
                className="session_container"
              >
                <Button
                  iconName="contact"
                  className="session"
                  onClick={() => {
                    console.log("Switch sessionId: ", ses);
                    setCurrentSessionId(ses.session_id);
                  }}
                >
                  {ses.title || "New Chat"}
                </Button>
              </div>
            ))}
          </div>
        </Box>
      )}
    </ContentLayout>
  );
};
