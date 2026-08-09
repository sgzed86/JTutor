const { app, Menu, shell } = require("electron");

function buildMenu({ onOpenSettings }) {
  const isMac = process.platform === "darwin";

  const template = [
    ...(isMac
      ? [
          {
            label: app.name,
            submenu: [
              { role: "about" },
              { type: "separator" },
              { label: "Settings…", accelerator: "Cmd+,", click: onOpenSettings },
              { type: "separator" },
              { role: "hide" },
              { role: "hideOthers" },
              { type: "separator" },
              { role: "quit" },
            ],
          },
        ]
      : []),
    {
      label: "File",
      submenu: [
        ...(isMac ? [] : [{ label: "Settings…", accelerator: "Ctrl+,", click: onOpenSettings }, { type: "separator" }]),
        isMac ? { role: "close" } : { role: "quit" },
      ],
    },
    { role: "editMenu" },
    {
      label: "View",
      submenu: [
        { role: "reload" },
        { role: "forceReload" },
        { role: "toggleDevTools" },
        { type: "separator" },
        { role: "resetZoom" },
        { role: "zoomIn" },
        { role: "zoomOut" },
        { type: "separator" },
        { role: "togglefullscreen" },
      ],
    },
    { role: "windowMenu" },
    {
      role: "help",
      submenu: [
        {
          label: "Irodori materials (Japan Foundation)",
          click: () => shell.openExternal("https://www.irodori.jpf.go.jp/"),
        },
      ],
    },
  ];

  return Menu.buildFromTemplate(template);
}

module.exports = { buildMenu };
