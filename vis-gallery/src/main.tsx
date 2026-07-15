import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "uplot/dist/uPlot.min.css";
import "./styles.css";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
