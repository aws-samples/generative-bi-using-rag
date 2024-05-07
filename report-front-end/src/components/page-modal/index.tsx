import {
  Modal,
  Box,
  SpaceBetween,
  Button,
  Form,
  FormField,
  Input,
  RadioGroup,
  Textarea,
} from "@cloudscape-design/components";
import { useState } from "react";

const PageModal = (props: { setModalShow: any; modalShow: any }) => {
  const { setModalShow, modalShow } = props;
  const [inputValue, setInputValue] = useState("");
  const [radioValue, setRadioValue] = useState("second");
  const [txtAreaValue, setTxtAreaValue] = useState("");
  return (
    <Modal
      onDismiss={() => setModalShow(false)}
      visible={modalShow}
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button variant="link" onClick={() => setModalShow(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={() => setModalShow(false)}>
              Ok
            </Button>
          </SpaceBetween>
        </Box>
      }
      header="Modal title"
    >
      <Form>
        <SpaceBetween size={"l"}>
          <FormField
            description="This is a description."
            label="Form field label 1"
          >
            <Input
              value={inputValue}
              onChange={(event) => setInputValue(event.detail.value)}
              placeholder="This is a placeholder"
            />
          </FormField>
          <FormField
            description="This is a description."
            label="Form field label 2"
          >
            <RadioGroup
              onChange={({ detail }) => setRadioValue(detail.value)}
              value={radioValue}
              items={[
                { value: "first", label: "First choice" },
                { value: "second", label: "Second choice" },
                { value: "third", label: "Third choice" },
              ]}
            />
          </FormField>
          <FormField
            description="This is a description."
            label="Form field label 3"
          >
            <Textarea
              value={txtAreaValue}
              onChange={(event) => setTxtAreaValue(event.detail.value)}
              placeholder="This is a placeholder"
            />
          </FormField>
        </SpaceBetween>
      </Form>
    </Modal>
  );
};
export default PageModal;
