import { createContext, Dispatch, SetStateAction, useContext } from "react";
import { Session } from "../components/PanelSideNav/types";

export interface IGlobalContext {
  sessions: Session[];
  setSessions: Dispatch<SetStateAction<Session[]>>;
  currentSessionId: string;
  setCurrentSessionId: Dispatch<SetStateAction<string>>;
  isSearching: boolean;
  setIsSearching: Dispatch<SetStateAction<boolean>>;
}
export const GlobalContext = createContext<IGlobalContext | null>(null);

export const useGlobalContext = () => {
  const context = useContext(GlobalContext);
  if (!context) {
    throw new Error("useGlobalContext must be used within a GlobalContext");
  }
  return context;
};

export default useGlobalContext;
