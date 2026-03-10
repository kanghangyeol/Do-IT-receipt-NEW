#!/usr/bin/env bash
# doit-view 실행 스크립트 (macOS / Linux / Windows Git Bash)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# ── 1. Python 버전 확인 (3.9 이상 필요) ─────────────────────────
check_py_version() {
  "$1" -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" 2>/dev/null
}

SYSTEM_PY=""
for cmd in python3 python; do
  if command -v "$cmd" >/dev/null 2>&1 && check_py_version "$cmd"; then
    SYSTEM_PY="$cmd"
    break
  fi
done

if [ -z "$SYSTEM_PY" ]; then
  echo "[run_booth] Python 3.9+ 없음. pyenv로 자동 설치합니다..."
  if ! command -v pyenv >/dev/null 2>&1; then
    if command -v brew >/dev/null 2>&1; then
      brew install pyenv
    else
      curl -fsSL https://pyenv.run | bash
    fi
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init -)"
  fi
  pyenv install -s 3.12
  pyenv local 3.12
  export PATH="$HOME/.pyenv/shims:$HOME/.pyenv/bin:$PATH"
  eval "$(pyenv init -)"
  SYSTEM_PY="python"
fi

# ── 2. venv가 없으면 자동 생성 ──────────────────────────────────
if [ ! -x "$ROOT/.venv/bin/python" ] && [ ! -x "$ROOT/.venv/Scripts/python.exe" ]; then
  echo "[run_booth] 가상환경 생성 중..."
  "$SYSTEM_PY" -m venv "$ROOT/.venv"
fi

# ── 3. Python 선택 (venv 우선) ──────────────────────────────────
if   [ -x "$ROOT/.venv/bin/python" ];          then PY="$ROOT/.venv/bin/python"
elif [ -x "$ROOT/venv/bin/python" ];           then PY="$ROOT/venv/bin/python"
elif [ -x "$ROOT/.venv/Scripts/python.exe" ];  then PY="$ROOT/.venv/Scripts/python.exe"
elif [ -x "$ROOT/venv/Scripts/python.exe" ];   then PY="$ROOT/venv/Scripts/python.exe"
else                                                 PY="$SYSTEM_PY"
fi

echo "[run_booth] Python: $PY ($($PY --version 2>&1))"

# ── 4. 의존성 자동 확인 / 설치 ───────────────────────────────────
if ! "$PY" -c "import PySide6, cv2, PIL, serial" 2>/dev/null; then
  echo "[run_booth] 필요한 패키지를 설치합니다..."
  "$PY" -m pip install --upgrade pip --quiet
  "$PY" -m pip install -r "$ROOT/requirements.txt" --quiet
fi

# ── 3. macOS: Qt 플러그인 hidden 플래그 제거 (pip 설치 후 발생하는 문제 방지) ──
# PySide6 Qt 플러그인 파일에 hidden 플래그가 설정되면 Qt가 파일을 인식 못함
if [ "$(uname)" = "Darwin" ]; then
  PS6_PLUG="$("$PY" - 2>/dev/null <<'PYEOF'
import importlib.util
from pathlib import Path
spec = importlib.util.find_spec("PySide6")
if spec and spec.submodule_search_locations:
    p = Path(next(iter(spec.submodule_search_locations))) / "Qt" / "plugins"
    if p.exists():
        print(p)
PYEOF
)"
  if [ -n "$PS6_PLUG" ]; then
    find "$PS6_PLUG" -name "*.dylib" -exec chflags nohidden {} \; 2>/dev/null || true
  fi
fi

# ── 4. 디버그 모드: USE_QT_DEBUG=1 bash run_booth.sh ─────────────
[ "${USE_QT_DEBUG:-0}" = "1" ] && export QT_DEBUG_PLUGINS=1

# ── 5. 실행 ──────────────────────────────────────────────────────
# Qt cocoa 플러그인 로딩은 app.py 내부에서 ctypes 프리로드로 처리됨
echo "[run_booth] 앱 시작..."
exec "$PY" "$ROOT/app.py"
