import { BrowserRouter, Route, Routes, } from "react-router-dom";
import Playground from "./pages/chatbot/playground";
import CustomTopNavigation from "./components/top-navigation";
import "./app.scss";

function App() {

  return (
    <div style={{ height: "100%" }}>
      <BrowserRouter>
        <CustomTopNavigation />
        <div style={{ height: "56px", backgroundColor: "#000716" }}>&nbsp;</div>
        <div>
          <Routes>
            <Route index path="/" element={<Playground />} />
          </Routes>
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;
