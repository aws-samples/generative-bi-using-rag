import {
  ContentLayout,
  SpaceBetween,
  Header,
  Button,
  Alert,
  Container,
  Link,
} from "@cloudscape-design/components";
import React from "react";

const DefaultPage = () => {
  return (
    <ContentLayout
      header={
        <SpaceBetween size="m">
          <Header
            variant="h1"
            info={<Link>Info</Link>}
            description="This is a generic description used in the header."
            actions={<Button variant="primary">Button</Button>}
          >
            How to send request
          </Header>

          <Alert statusIconAriaLabel="Info">This is a generic alert.</Alert>
        </SpaceBetween>
      }
    >
      <SpaceBetween size="m">
        <Container
          header={
            <Header variant="h2" description="Container description">
              How to send request
            </Header>
          }
        >
          Container content
        </Container>
      </SpaceBetween>
    </ContentLayout>
  );
};

export default DefaultPage;
