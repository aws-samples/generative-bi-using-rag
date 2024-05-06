import { BrowserRouter, Route, Routes } from "react-router-dom";
import PageLayout from "../page-layout";
import TableList from "../table-list";
import DefaultPage from "../default-page";
import ChartPage from "../chart-page";

const PageRouter = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={<PageLayout content={<DefaultPage></DefaultPage>} />}
        />
        <Route
          path="/page1"
          element={<PageLayout content={<TableList></TableList>} />}
        />
        <Route
          path="/page2"
          element={<PageLayout content={<ChartPage></ChartPage>} />}
        />
      </Routes>
    </BrowserRouter>
  );
};

export default PageRouter;
