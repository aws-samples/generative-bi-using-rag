import { UseAuthenticator } from "@aws-amplify/ui-react-core";
import { useState } from "react";
import { Toaster } from "react-hot-toast";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { v4 as uuid } from "uuid";
import "./app.scss";
import BaseAppLayout from "./components/BaseAppLayout";
import PanelConfigs from "./components/PanelConfigs";
import { PanelSideNav } from "./components/PanelSideNav";
import { Session } from "./components/PanelSideNav/types";
import SectionChat from "./components/SectionChat";
import TopNav from "./components/TopNav";
import { GlobalContext } from "./hooks/useGlobalContext";
import useUnauthorized from "./hooks/useUnauthorized";

export type SignOut = UseAuthenticator["signOut"];

const App: React.FC = () => {
  useUnauthorized();
  return (
    <div style={{ height: "100%" }}>
      <BrowserRouter>
        <Toaster />
        <TopNav />
        <div style={{ height: "56px", backgroundColor: "#000716" }}>&nbsp;</div>
        <div>
          <Routes>
            <Route index path="/" element={<Playground />} />
          </Routes>
        </div>
      </BrowserRouter>
    </div>
  );
};

export default App;

const initSession = () => ({
  session_id: uuid(),
  title: "New Chat",
  messages: [],
});

function Playground() {
  const [toolsHide, setToolsHide] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([initSession()]);
  const [currentSessionId, setCurrentSessionId] = useState(
    sessions[0].session_id
  );
  return (
    <GlobalContext.Provider
      value={{
        sessions,
        setSessions,
        currentSessionId,
        setCurrentSessionId,
        isSearching,
        setIsSearching,
      }}
    >
      <BaseAppLayout
        navigation={<PanelSideNav />}
        content={<SectionChat {...{ toolsHide, setToolsHide }} />}
        tools={<PanelConfigs setToolsHide={setToolsHide} />}
        toolsHide={toolsHide}
        setToolsHide={setToolsHide}
      />
    </GlobalContext.Provider>
  );
}
