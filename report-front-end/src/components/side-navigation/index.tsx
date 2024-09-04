import { Sessions } from "../session-panel/sessions";
import { ContentLayout, Header } from "@cloudscape-design/components";
import { Session } from "../session-panel/types";
import { Dispatch, SetStateAction } from "react";

export default function NavigationPanel(
  props: {
    sessions: Session[];
    setSessions: Dispatch<SetStateAction<Session[]>>;
    currentSessionId: string;
    setCurrentSessionId: Dispatch<SetStateAction<string>>;
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
        currentSessionId={props.currentSessionId}
        setCurrentSessionId={props.setCurrentSessionId}
      />
    </ContentLayout>
  );
}
