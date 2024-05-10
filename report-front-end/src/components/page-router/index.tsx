import { BrowserRouter, Route, Routes } from "react-router-dom";
import PageLayout from "../page-layout";
import Chat from "../chatbot/chat";
import { useState } from "react";

const PageRouter = () => {
  const [toolsHide, setToolsHide] = useState(true);
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <PageLayout
              content={<Chat setToolsHide={setToolsHide} />}
              toolsHide={toolsHide}
              setToolsHide={setToolsHide}
            />
          }
        />
      </Routes>
    </BrowserRouter>
  );
};

export default PageRouter;
