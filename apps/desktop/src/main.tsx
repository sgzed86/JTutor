import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";
import App from "./App";
import { ErrorBoundary } from "./components/feedback/ErrorBoundary";
import { SettingsProvider } from "./state/SettingsProvider";
import "@fontsource/shippori-mincho/japanese-500.css";
import "@fontsource/shippori-mincho/japanese-700.css";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "./styles/tokens.css";
import "./styles/themes.css";
import "./styles/base.css";
import "./styles/components.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <SettingsProvider>
        <HashRouter>
          <App />
        </HashRouter>
      </SettingsProvider>
    </ErrorBoundary>
  </React.StrictMode>,
);
