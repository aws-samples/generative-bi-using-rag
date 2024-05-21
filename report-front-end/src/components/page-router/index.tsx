import { BrowserRouter, Route, Routes } from "react-router-dom";
import PageLayout from "../page-layout";
import Chat from "../chatbot-panel/chat";
import React, { useState } from "react";
import CustomTopNavigation from "../../components/top-navigation";

const PageRouter = () => {
  const [toolsHide, setToolsHide] = useState(true);
  return (
    <BrowserRouter>
      <CustomTopNavigation />
      <div style={{ height: "56px", backgroundColor: "#000716" }}>&nbsp;</div>
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
