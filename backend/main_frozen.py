"""Entry point for the frozen (PyInstaller) backend.

Kept deliberately small: it parses the arguments the Electron supervisor passes,
puts the paths into the environment, and only then imports the app.

`backend/app/main.py` and `backend/app/config.py` both resolve `JTUTOR_ROOT` at
*import* time, so the environment has to be set before the first
`import backend.app`. Deferring the import into `main()` guarantees that.
"""

from __future__ import annotations

import argparse
import os
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jtutor-backend", description="Jtutor local API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True, help="port chosen by the desktop supervisor")
    parser.add_argument("--root", default=None, help="folder holding content/ and ui/")
    parser.add_argument("--data-dir", default=None, help="writable folder for the database, logs and caches")
    parser.add_argument("--assets-dir", default=None, help="folder holding the Irodori PDFs and MP3s")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.root:
        os.environ["JTUTOR_ROOT"] = args.root
    elif getattr(sys, "frozen", False):
        # One-folder PyInstaller build: resources sit next to the executable.
        os.environ.setdefault("JTUTOR_ROOT", os.path.dirname(sys.executable))
    if args.data_dir:
        os.environ["JTUTOR_DATA_DIR"] = args.data_dir
    if args.assets_dir:
        os.environ["JTUTOR_ASSETS_DIR"] = args.assets_dir

    import uvicorn

    from backend.app.main import app

    # The app object, not "module:app" — the string form re-imports by module
    # path, which does not resolve inside a frozen interpreter.
    uvicorn.run(app, host=args.host, port=args.port, log_config=None, access_log=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
