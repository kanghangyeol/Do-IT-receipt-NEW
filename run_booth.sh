#!/usr/bin/env bash
set -euo pipefail

# Run from repo root
ROOT="$(cd "$(dirname "$0")" && pwd)"

# Load .env if present (kept out of git)
if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$ROOT/.env"
  set +a
fi

# Pick Python (prefer project venv)
if [ -n "${PYTHON:-}" ]; then
  PY="$PYTHON"
elif [ -x "$ROOT/.venv/bin/python" ]; then
  PY="$ROOT/.venv/bin/python"
elif [ -x "$ROOT/venv/bin/python" ]; then
  PY="$ROOT/venv/bin/python"
elif [ -x "$ROOT/.venv/Scripts/python.exe" ]; then
  PY="$ROOT/.venv/Scripts/python.exe"
elif [ -x "$ROOT/venv/Scripts/python.exe" ]; then
  PY="$ROOT/venv/Scripts/python.exe"
else
  if command -v python3.12 >/dev/null 2>&1; then
    PY="python3.12"
  elif command -v python3 >/dev/null 2>&1; then
    PY="python3"
  else
    PY="python"
  fi
fi

USE_QT_DEBUG=${USE_QT_DEBUG:-0}
if [ "$USE_QT_DEBUG" = "1" ]; then
  export QT_DEBUG_PLUGINS=1
fi

# Qt 플러그인/플랫폼 경로 설정 (PySide6 기준)
PLUG_ROOT="$("$PY" - <<'PY'
import importlib.util
from pathlib import Path
spec = importlib.util.find_spec("PySide6")
if spec and spec.submodule_search_locations:
    base = Path(next(iter(spec.submodule_search_locations)))
    print(base / "Qt" / "plugins")
PY
)"
if [ -n "$PLUG_ROOT" ] && [ -d "$PLUG_ROOT" ]; then
  export QT_PLUGIN_PATH="$PLUG_ROOT"
  if [ -d "$PLUG_ROOT/platforms" ]; then
    export QT_QPA_PLATFORM_PLUGIN_PATH="$PLUG_ROOT/platforms"
  fi
fi

# macOS: Qt 프레임워크 경로 주입 + 기본 cocoa 플랫폼 지정
if [ "$(uname)" = "Darwin" ]; then
  QT_LIB_DIR="$("$PY" - <<'PY'
import importlib.util
from pathlib import Path
spec = importlib.util.find_spec("PySide6")
if spec and spec.submodule_search_locations:
    base = Path(next(iter(spec.submodule_search_locations)))
    print(base / "Qt" / "lib")
PY
)"
  if [ -d "$QT_LIB_DIR" ]; then
    export DYLD_FRAMEWORK_PATH="$QT_LIB_DIR"
  fi
  if [ -z "${QT_QPA_PLATFORM:-}" ]; then
    export QT_QPA_PLATFORM=cocoa
  fi
fi

exec "$PY" "$ROOT/app.py"
