import "./app.scss";
import PageRouter from "./pages/page-router";
import CustomTopNavigation from "./components/top-navigation";
import { BrowserRouter } from "react-router-dom";

function App() {

  return (
    <div style={{ height: "100%" }}>
      <BrowserRouter>
        <CustomTopNavigation />
        <div style={{ height: "56px", backgroundColor: "#000716" }}>&nbsp;</div>
        <div>
          <PageRouter />
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;
