import { useEffect, useState } from "react";
import ConfigPanel from "../../components/config-panel";
import BaseAppLayout from "../../components/app-layout";
import Chat from "../../components/chatbot-panel/chat";
import ErrorPage from "../error-page";
import { useLocation } from "react-router-dom";
import { Global } from "../../common/constant/global";

export default function Playground() {
  const [toolsHide, setToolsHide] = useState(true);
  const [authentication, setAuthentication] = useState(true);

  const { search } = useLocation();
  const params = new URLSearchParams(search);
  Global.profile = params.get("profile") || "";

  const showErrorPage = (isAuthentication: boolean) => {
    setAuthentication(isAuthentication);
  };

  useEffect(() => {
    window.addEventListener("unauthorized", () => showErrorPage(false));
    return () => {
      window.removeEventListener("unauthorized", () => showErrorPage(false));
    };
  }, []);

  return (
    authentication ?
      <BaseAppLayout
        info={<ConfigPanel setToolsHide={setToolsHide} />}
        content={<Chat toolsHide={toolsHide} setToolsHide={setToolsHide} />}
        toolsHide={toolsHide}
        setToolsHide={setToolsHide}
      /> : <ErrorPage />
  );
}
