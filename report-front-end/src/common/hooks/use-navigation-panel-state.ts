import { useState } from "react";
import { Storage } from "../helpers/storage";
import { NavigationPanelState } from "../types";

export function useNavigationPanelState(): [
  NavigationPanelState,
  (state: Partial<NavigationPanelState>) => void,
] {
  const [currentState, setCurrentState] = useState(
    Storage.getNavigationPanelState()
  );

  const onChange = (state: Partial<NavigationPanelState>) => {
    setCurrentState(Storage.setNavigationPanelState(state));
  };

  return [currentState, onChange];
}
