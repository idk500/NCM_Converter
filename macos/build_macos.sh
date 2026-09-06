#!/bin/bash
# Build the macOS deliverables:
#   dist/ncm_converter/            — CLI (same UX as the Windows exe, run from Terminal)
#   dist/NCM Converter.app         — .app wrapper (double-click opens Terminal, proper icon)
#   dist/NCM_Converter-macos.zip   — both, ready to distribute
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt pyinstaller pillow

# Icon (idempotent; Pillow saves ICNS with all resolutions)
.venv/bin/python - <<'PY'
from pathlib import Path
from PIL import Image
out = Path('macos/ncm_converter.icns')
if not out.exists():
    img = Image.open('ncm_converter.ico').convert('RGBA').resize((512, 512), Image.LANCZOS)
    out.parent.mkdir(exist_ok=True)
    img.save(out, format='ICNS')
PY

.venv/bin/pyinstaller --noconfirm macos/ncm_converter_mac.spec

APP="dist/NCM Converter.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp macos/Info.plist "$APP/Contents/Info.plist"
cp macos/ncm_converter.icns "$APP/Contents/Resources/ncm_converter.icns"
cp -R dist/ncm_converter "$APP/Contents/MacOS/ncm_converter"
cp macos/launcher "$APP/Contents/MacOS/launcher"
chmod +x "$APP/Contents/MacOS/launcher"

# PyInstaller output already carries linker ad-hoc signatures (required on arm64).
# Sign only the outer bundle; --deep chokes on PyInstaller's _internal layout.
codesign --force -s - "$APP" 2>/dev/null || true

cd dist
rm -f NCM_Converter-macos.zip
zip -qry NCM_Converter-macos.zip "NCM Converter.app"
cd ..
echo "OK: $APP and dist/NCM_Converter-macos.zip"
