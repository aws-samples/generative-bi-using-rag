import { BrowserRouter, Route, Routes } from "react-router-dom";
import PageLayout from "../page-layout";
import Chat from "../chatbot/chat";

const PageRouter = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<PageLayout content={<Chat></Chat>} />} />
      </Routes>
    </BrowserRouter>
  );
};

export default PageRouter;
