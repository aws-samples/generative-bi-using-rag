import {
  applyDensity,
  applyMode,
  Density,
  Mode,
} from "@cloudscape-design/global-styles";
import { NavigationPanelState } from "../types";
import { APP_STYLE_DEFAULT_COMPACT } from "../constant/constants";

const PREFIX = "genai-chatbot";
const THEME_STORAGE_NAME = `${PREFIX}-themes`;
const DENSITY_STORAGE_NAME = `${PREFIX}-density`;
const NAVIGATION_PANEL_STATE_STORAGE_NAME = `${PREFIX}-navigation-panel-state`;

export abstract class Storage {
  static getTheme() {
    const value = localStorage.getItem(THEME_STORAGE_NAME) ?? Mode.Light;
    return value === Mode.Dark ? Mode.Dark : Mode.Light;
  }

  static applyTheme(theme: Mode) {
    localStorage.setItem(THEME_STORAGE_NAME, theme);
    applyMode(theme);

    document.documentElement.style.setProperty(
      "--app-color-scheme",
      theme === Mode.Dark ? "dark" : "light"
    );

    return theme;
  }

  static getDensity(): Density {
    let density = localStorage.getItem(DENSITY_STORAGE_NAME) as Density | null;
    if (!density) {
      density = APP_STYLE_DEFAULT_COMPACT
        ? Density.Compact
        : Density.Comfortable;
    }
    return density;
  }
  static applyDensity(density: Density) {
    localStorage.setItem(DENSITY_STORAGE_NAME, density);
    applyDensity(density);
  }

  static getNavigationPanelState(): NavigationPanelState {
    const value =
      localStorage.getItem(NAVIGATION_PANEL_STATE_STORAGE_NAME) ??
      JSON.stringify({
        collapsed: true,
      });

    let state: NavigationPanelState | null = null;
    try {
      state = JSON.parse(value);
    } catch {
      state = {};
    }

    return state ?? {};
  }

  static setNavigationPanelState(state: Partial<NavigationPanelState>) {
    const currentState = this.getNavigationPanelState();
    const newState = { ...currentState, ...state };
    const stateStr = JSON.stringify(newState);
    localStorage.setItem(NAVIGATION_PANEL_STATE_STORAGE_NAME, stateStr);

    return newState;
  }
}
