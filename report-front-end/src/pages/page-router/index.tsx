import { Route, Routes, useNavigate } from "react-router-dom";
import Playground from "../chatbot-page/playground";
import ErrorPage from "../error-page";
import { useEffect } from "react";

const PageRouter = () => {

  const navigate = useNavigate();
  const showErrorPage = () => {
    navigate('/error');
  };

  useEffect(() => {
    window.addEventListener("unauthorized", showErrorPage);
    return () => {
      window.removeEventListener("unauthorized", showErrorPage);
    };
  }, []);

  return (
    <Routes>
      <Route index path="/" element={<Playground />} />
      <Route index path="/error" element={<ErrorPage />} />
    </Routes>
  );
};

export default PageRouter;
