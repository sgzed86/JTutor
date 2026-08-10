/**
 * Launch Electron in Vite-dev mode (HMR + detach DevTools).
 * Used by `npm run dev`; the desktop shortcut uses Electron directly instead.
 */
const { spawn } = require("child_process");
const electron = require("electron");

process.env.JTUTOR_DEV = "1";

const child = spawn(electron, ["."], {
  stdio: "inherit",
  env: process.env,
  windowsHide: false,
});

child.on("exit", (code, signal) => {
  if (signal) process.exit(1);
  process.exit(code ?? 0);
});
