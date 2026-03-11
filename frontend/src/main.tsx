import React from "react";
import ReactDOM from "react-dom/client";

import "@fontsource-variable/fraunces/index.css";
import "@fontsource-variable/manrope/index.css";

import { App } from "@/app/App";
import "@/app/styles.css";
import { registerServiceWorker } from "@/shared/lib/pwa";

registerServiceWorker();

ReactDOM.createRoot(document.getElementById("app") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
