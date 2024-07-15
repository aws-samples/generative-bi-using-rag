import { Route, Routes } from "react-router-dom";
import Playground from "../chatbot-page/playground";

const PageRouter = () => {

  return (
    <Routes>
      <Route index path="/" element={<Playground />} />
    </Routes>
  );
};

export default PageRouter;
