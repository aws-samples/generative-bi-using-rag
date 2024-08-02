import { Sessions } from "../session-panel/sessions";
import { ContentLayout, Header } from "@cloudscape-design/components";
import { Session } from "../session-panel/types";
import { Dispatch, SetStateAction } from "react";

export default function NavigationPanel(
  props: {
    sessions: Session[];
    setSessions: Dispatch<SetStateAction<Session[]>>;
    currentSession: number;
    setCurrentSession: Dispatch<SetStateAction<number>>;
  }) {

  return (
    <ContentLayout
      defaultPadding
      disableOverlap
      headerVariant="divider"
      header={
        <Header variant="h3">
          Sessions
        </Header>
      }
    >
      <Sessions
        sessions={props.sessions}
        setSessions={props.setSessions}
        currentSession={props.currentSession}
        setCurrentSession={props.setCurrentSession}
      />
    </ContentLayout>
  );
}
