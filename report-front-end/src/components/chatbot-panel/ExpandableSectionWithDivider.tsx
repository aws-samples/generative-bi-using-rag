import { Divider } from "@aws-amplify/ui-react";
import {
  ExpandableSection,
  ExpandableSectionProps,
} from "@cloudscape-design/components";
import React from "react";

const ExpandableSectionWithDivider: React.FC<
  ExpandableSectionProps & { withDivider?: boolean; label?: string }
> = ({ withDivider = true, label, children, ...props }) => {
  return (
    <div style={{}}>
      <ExpandableSection {...props}>
        <div style={{ padding: "0 20px" }}>
          {children}
          {!withDivider ? null : (
            <div style={{ paddingTop: "12px" }}>
              <Divider label={label} />
            </div>
          )}
        </div>
      </ExpandableSection>
    </div>
  );
};

export default ExpandableSectionWithDivider;
