# PyInstaller spec for the Jtutor backend.
#
# One-FOLDER build on purpose. A one-file build unpacks several hundred MB to a
# temp directory on every launch, which adds seconds to startup and is a common
# antivirus false positive on Windows.
#
#   pyinstaller packaging/jtutor-backend.spec --noconfirm --distpath dist-backend
#
# The result is dist-backend/jtutor-backend/, which electron-builder copies into
# the installer as `backend-dist`.

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(os.environ.get("JTUTOR_SPEC_ROOT", os.getcwd())).resolve()
LITE = os.environ.get("JTUTOR_LITE_BUILD") == "1"

# Modules PyInstaller cannot discover from static imports: uvicorn resolves its
# loop/protocol/lifespan implementations by string at runtime, and the ML stack
# is loaded lazily.
hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "anyio._backends._asyncio",
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.sql.default_comparator",
    "pydantic.deprecated.decorator",
    "fsrs",
    "yaml",
    "multipart",
]

if not LITE:
    hiddenimports += [
        "faster_whisper",
        "ctranslate2",
        "av",
        "onnxruntime",
        "tokenizers",
    ]

datas = []
binaries = []

for package in ("fsrs",):
    datas += collect_data_files(package)

if not LITE:
    for package in ("faster_whisper", "tokenizers"):
        try:
            datas += collect_data_files(package)
            hiddenimports += collect_submodules(package)
        except Exception:  # noqa: BLE001 - optional in a lite build
            pass

excludes = [
    "tkinter",
    "matplotlib",
    "notebook",
    "IPython",
    "pytest",
    "setuptools",
]
if LITE:
    excludes += ["faster_whisper", "ctranslate2", "onnxruntime", "av", "torch", "tokenizers"]

block_cipher = None

a = Analysis(
    [str(ROOT / "backend" / "main_frozen.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="jtutor-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=sys.platform != "win32",  # no console window on Windows
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="jtutor-backend",
)
