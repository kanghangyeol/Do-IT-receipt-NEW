# app.py
import sys, os
from pathlib import Path


def _preload_qt_frameworks() -> None:
    """
    macOS SIP 환경에서 DYLD_FRAMEWORK_PATH가 차단돼도
    Qt 핵심 프레임워크를 ctypes로 미리 로드해 cocoa 플러그인 로딩 오류를 방지.
    """
    if sys.platform != "darwin":
        return
    try:
        import importlib.util, ctypes
        spec = importlib.util.find_spec("PySide6")
        if not (spec and spec.submodule_search_locations):
            return
        base    = Path(next(iter(spec.submodule_search_locations)))
        qt_lib  = base / "Qt" / "lib"
        qt_plug = base / "Qt" / "plugins"

        # Qt 플러그인 경로 환경변수 설정 (SIP 영향 없음)
        if qt_plug.exists():
            os.environ.setdefault("QT_PLUGIN_PATH", str(qt_plug))
        plat_dir = qt_plug / "platforms"
        if plat_dir.exists():
            os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(plat_dir))
        os.environ.setdefault("QT_QPA_PLATFORM", "cocoa")

        # Qt 프레임워크 미리 로드 → cocoa 플러그인이 의존성 탐색 시 이미 메모리에 있게 됨
        for fw in ["QtCore", "QtDBus", "QtGui", "QtWidgets", "QtOpenGL", "QtPrintSupport"]:
            fw_bin = qt_lib / f"{fw}.framework" / fw
            if fw_bin.exists():
                try:
                    ctypes.CDLL(str(fw_bin))
                except Exception:
                    pass
    except Exception:
        pass


_preload_qt_frameworks()

from PySide6 import QtWidgets
from ui_booth import BoothCam

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = BoothCam()
    w.show()
    sys.exit(app.exec())