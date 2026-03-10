import os, sys, tempfile
from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui

import cv2, time
from PIL import Image

from compose import compose_receipt_two_photos
from printer_io import print_image_usb, list_usb_candidate_ports

# ── SVG 에셋 자동 생성 ──────────────────────────────────────────
_ASSET_DIR = Path(tempfile.gettempdir()) / "doit_booth_assets"
_ASSET_DIR.mkdir(exist_ok=True)
(_ASSET_DIR / "check.svg").write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
    '<polyline points="2,9 6,13 14,3" fill="none" stroke="white" '
    'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>')
(_ASSET_DIR / "arrow_up.svg").write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12">'
    '<polyline points="1,8 6,3 11,8" fill="none" stroke="#aab8d0" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')
(_ASSET_DIR / "arrow_down.svg").write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12">'
    '<polyline points="1,4 6,9 11,4" fill="none" stroke="#aab8d0" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')
_CHECK  = str(_ASSET_DIR / "check.svg").replace("\\", "/")
_ARR_UP = str(_ASSET_DIR / "arrow_up.svg").replace("\\", "/")
_ARR_DN = str(_ASSET_DIR / "arrow_down.svg").replace("\\", "/")

# ===== 고정값 / 기본값 =====
DEFAULT_SHORT_TEXT  = "JUST Do-IT!"
DEFAULT_FONT_PATH   = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
if sys.platform.startswith("win"):
    DEFAULT_FONT_PATH = r"C:\Windows\Fonts\malgun.ttf"
elif sys.platform.startswith("linux"):
    DEFAULT_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

PAPER_WIDTH        = 576
DEFAULT_MARGIN     = 7
DEFAULT_GAP        = 4
DEFAULT_PHOTO_GAP  = 8
DEFAULT_LOGO_PATH  = "Doit_logo.jpeg"
DEFAULT_LETTERBOX  = 0
DEFAULT_LOGO_MAX_H = 160

_env_font = os.getenv("FONT_PATH")
if _env_font:
    DEFAULT_FONT_PATH = _env_font

# ===== 스타일 =====
APP_STYLE = """
QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Apple SD Gothic Neo', 'DejaVu Sans', sans-serif;
    font-size: 13px;
}
QLabel { color: #e0e0e0; }

/* ── 기본 버튼 ── */
QPushButton {
    background-color: #1e2a45;
    color: #dde4f0;
    border: 2px solid #3a5080;
    border-radius: 10px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton:hover  { background-color: #253560; border-color: #6080c0; color: #ffffff; }
QPushButton:pressed{ background-color: #304080; border-color: #80a0e0; color: #ffffff; }
QPushButton:disabled{ background-color: #1a1a2e; color: #444; border-color: #2a2a3e; }

/* ── 촬영 (빨강) ── */
QPushButton#snapBtn {
    background-color: #c0203a;
    color: #ffffff;
    border: 2px solid #e84060;
    border-radius: 10px;
    font-size: 16px;
    font-weight: bold;
}
QPushButton#snapBtn:hover   { background-color: #e02040; border-color: #ff7090; }
QPushButton#snapBtn:pressed { background-color: #901830; border-color: #c0203a; }
QPushButton#snapBtn:disabled{ background-color: #4a1020; color: #664; border-color: #6a2030; }

/* ── 출력 (파랑) ── */
QPushButton#printBtn {
    background-color: #0d3060;
    color: #ffffff;
    border: 2px solid #3a80d0;
    border-radius: 10px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#printBtn:hover  { background-color: #1a4a90; border-color: #60a0ff; }
QPushButton#printBtn:disabled{ background-color: #0a1a30; color: #445; border-color: #1a2a40; }

/* ── 초기화 (회색) ── */
QPushButton#resetBtn {
    background-color: #252535;
    color: #b0b8c8;
    border: 2px solid #4a5068;
    border-radius: 10px;
    font-size: 13px;
}
QPushButton#resetBtn:hover { background-color: #303050; border-color: #7080a0; color: #e0e8ff; }

/* ── 작은 보조 버튼 ── */
QPushButton#smallBtn {
    background-color: #1e2a45;
    color: #aab8d0;
    border: 2px solid #3a5080;
    border-radius: 8px;
    font-size: 12px;
    padding: 4px 8px;
}
QPushButton#smallBtn:hover { background-color: #253560; border-color: #6080c0; color: #ffffff; }

QComboBox {
    background-color: #1e2a45;
    color: #dde4f0;
    border: 2px solid #3a5080;
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 28px;
}
QComboBox:hover { border-color: #e84060; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background-color: #1e2a45;
    color: #dde4f0;
    border: 1px solid #3a5080;
    selection-background-color: #304080;
}

QSpinBox {
    background-color: #1e2a45;
    color: #dde4f0;
    border: 2px solid #3a5080;
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 28px;
}
QSpinBox:focus { border-color: #e84060; }
QSpinBox::up-button, QSpinBox::down-button {
    width: 18px; border: none; background: #253560;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: #e84060; }

QTextEdit {
    background-color: #1e2a45;
    color: #dde4f0;
    border: 2px solid #3a5080;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #e84060;
}
QTextEdit:focus { border-color: #e84060; }

QLineEdit {
    background-color: #1e2a45;
    color: #dde4f0;
    border: 2px solid #3a5080;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 28px;
}
QLineEdit:focus { border-color: #e84060; }

QCheckBox { color: #dde4f0; spacing: 8px; }
QCheckBox::indicator {
    width: 18px; height: 18px; border-radius: 4px;
    border: 2px solid #3a5080; background: #1e2a45;
}
QCheckBox::indicator:checked  { background: #e84060; border-color: #e84060; }
QCheckBox::indicator:hover    { border-color: #e84060; }

QScrollBar:vertical { background: #1e2a45; width: 6px; border-radius: 3px; }
QScrollBar::handle:vertical { background: #3a5080; border-radius: 3px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

APP_STYLE += f"""
QCheckBox::indicator:checked {{
    background: #e84060; border-color: #e84060;
    image: url({_CHECK});
}}
QSpinBox::up-button {{
    width: 20px; border: none; background: #253560;
    image: url({_ARR_UP});
}}
QSpinBox::down-button {{
    width: 20px; border: none; background: #253560;
    image: url({_ARR_DN});
}}
QSpinBox::up-button:hover   {{ background: #e84060; }}
QSpinBox::down-button:hover {{ background: #e84060; }}
"""


def open_capture(idx: int):
    if sys.platform.startswith("darwin"):
        return cv2.VideoCapture(idx, cv2.CAP_AVFOUNDATION)
    if sys.platform.startswith("win"):
        return cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    return cv2.VideoCapture(idx)


class CountdownOverlay(QtWidgets.QWidget):
    finished = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self._count = 0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.hide()

    def start(self, from_n: int = 3):
        self._count = from_n
        self.show()
        self.update()
        self._timer.start(1000)

    def _tick(self):
        self._count -= 1
        if self._count <= 0:
            self._timer.stop()
            self.hide()
            self.finished.emit()
        else:
            self.update()

    def paintEvent(self, event):
        if self._count <= 0:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 130))
        font = QtGui.QFont("Arial", 160, QtGui.QFont.Bold)
        painter.setFont(font)
        painter.setPen(QtGui.QColor(232, 64, 96))
        painter.drawText(self.rect(), QtCore.Qt.AlignCenter, str(self._count))
        painter.end()


class FlashOverlay(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self._opacity = 0.0
        self._anim = QtCore.QPropertyAnimation(self, b"opacity")
        self._anim.setDuration(300)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self._anim.finished.connect(self.hide)
        self.hide()

    def get_opacity(self): return self._opacity
    def set_opacity(self, v): self._opacity = v; self.update()
    opacity = QtCore.Property(float, get_opacity, set_opacity)

    def flash(self):
        self.show(); self._anim.stop(); self._opacity = 1.0; self._anim.start()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.fillRect(self.rect(), QtGui.QColor(255, 255, 255, int(self._opacity * 220)))
        p.end()


class BoothCam(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("두잇 영수증 사진관")
        # 세로를 충분히 높게 + 최대화 시작
        self.resize(1600, 1000)
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(APP_STYLE)

        self.base_dir = Path(__file__).resolve().parent
        self.captures_dir = self.base_dir / "captures"
        self.captures_dir.mkdir(parents=True, exist_ok=True)

        self.cap = None
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.mirror = True
        self.last_frame = None
        self.captured_images: list[tuple[Path, object]] = []
        self.max_shots = 2
        self._counting_down = False

        # ════════════════════════════════════════
        # 왼쪽: 카메라 프리뷰
        # ════════════════════════════════════════
        self.video_container = QtWidgets.QWidget()
        self.video_container.setStyleSheet("background:#0a0a18; border-radius:14px;")
        vc_layout = QtWidgets.QVBoxLayout(self.video_container)
        vc_layout.setContentsMargins(0, 0, 0, 0)

        self.video = QtWidgets.QLabel("카메라 연결 중...")
        self.video.setAlignment(QtCore.Qt.AlignCenter)
        self.video.setStyleSheet("background:transparent; color:#444; font-size:18px;")
        self.video.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        vc_layout.addWidget(self.video)

        self.countdown    = CountdownOverlay(self.video)
        self.flash_overlay = FlashOverlay(self.video)
        self.countdown.finished.connect(self._do_capture)

        # ════════════════════════════════════════
        # 오른쪽 패널 위젯들
        # ════════════════════════════════════════

        # 카메라 선택
        self.device_combo = QtWidgets.QComboBox()

        # 카운트다운 스핀박스
        self.countdown_spin = QtWidgets.QSpinBox()
        self.countdown_spin.setRange(0, 10)
        self.countdown_spin.setValue(3)
        self.countdown_spin.setSuffix(" 초")

        # 남은 촬영 표시
        self.count_label = QtWidgets.QLabel("남은 촬영: 2장")
        self.count_label.setAlignment(QtCore.Qt.AlignCenter)
        self.count_label.setStyleSheet(
            "color:#e84060; font-size:14px; font-weight:bold;"
            "background:#200a12; border-radius:6px; padding:6px;"
        )

        # ── 정사각형 버튼 (120×80) ──
        BTN_W, BTN_H = 140, 80

        self.snap_btn = QtWidgets.QPushButton("📷\n촬영")
        self.snap_btn.setObjectName("snapBtn")
        self.snap_btn.setFixedSize(BTN_W, BTN_H)
        self.snap_btn.setToolTip("사진 촬영 (Space)")

        self.print_btn = QtWidgets.QPushButton("🖨\n출력")
        self.print_btn.setObjectName("printBtn")
        self.print_btn.setFixedSize(BTN_W, BTN_H)
        self.print_btn.setEnabled(False)

        self.reset_btn = QtWidgets.QPushButton("↺\n초기화")
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.setFixedSize(BTN_W, BTN_H)

        # 프린터 새로고침 버튼
        self.refresh_printer_btn = QtWidgets.QPushButton("🔌\n프린터 검색")
        self.refresh_printer_btn.setObjectName("smallBtn")
        self.refresh_printer_btn.setFixedSize(BTN_W, BTN_H)

        # ── 썸네일 (오른쪽 패널 상단, 세로로 2장) ──
        self.thumb_labels = []
        for i in range(2):
            lbl = QtWidgets.QLabel(f"사진 {i+1}")
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setStyleSheet(
                "background:#0a0a18; border:2px dashed #2a3a5e;"
                "border-radius:8px; color:#3a4a6e; font-size:14px;"
            )
            lbl.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            self.thumb_labels.append(lbl)

        # 문구
        self.short_edit = QtWidgets.QTextEdit()
        self.short_edit.setAcceptRichText(False)
        self.short_edit.setWordWrapMode(QtGui.QTextOption.WordWrap)
        self.short_edit.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.short_edit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.short_edit.setPlaceholderText("영수증 하단 문구")
        self.short_edit.setPlainText(DEFAULT_SHORT_TEXT)
        self.short_edit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        fm = self.short_edit.fontMetrics()
        self.short_edit.setFixedHeight(fm.lineSpacing() * 2 + 20)

        # 로고
        self.logo_edit = QtWidgets.QLineEdit(DEFAULT_LOGO_PATH)
        self.logo_btn  = QtWidgets.QPushButton("📁")
        self.logo_btn.setObjectName("smallBtn")
        self.logo_btn.setFixedWidth(40)

        # 프린터
        self.chk_printer    = QtWidgets.QCheckBox("USB 프린터 출력")
        self.chk_printer.setChecked(True)
        self.chk_auto_reset = QtWidgets.QCheckBox("출력 후 자동 초기화")
        self.chk_auto_reset.setChecked(True)

        self.copies_combo = QtWidgets.QComboBox()
        self.copies_combo.addItems([str(i) for i in range(1, 11)])
        self.copies_combo.setFixedWidth(70)

        # 프린터 포트 콤보
        self.printer_port_combo = QtWidgets.QComboBox()
        self.printer_port_combo.addItem("자동 탐색")

        # 상태바
        self.status = QtWidgets.QLabel("✔ 준비")
        self.status.setWordWrap(True)
        self.status.setStyleSheet(
            "color:#4da6ff; background:#081828; border-radius:6px;"
            "padding:6px 10px; font-size:12px;"
        )

        # 프린터 포트 초기 탐색 (self.status 생성 이후)
        self._refresh_printer_ports()

        # ════════════════════════════════════════
        # 오른쪽 레이아웃 조립
        # ════════════════════════════════════════
        right = QtWidgets.QVBoxLayout()
        right.setSpacing(8)
        right.setContentsMargins(10, 10, 10, 10)

        # 카메라 선택
        dev_row = QtWidgets.QHBoxLayout()
        dev_lbl = QtWidgets.QLabel("카메라:")
        dev_lbl.setStyleSheet("color:#888; font-size:12px;")
        dev_row.addWidget(dev_lbl)
        dev_row.addWidget(self.device_combo, 1)
        right.addLayout(dev_row)

        # 카운트다운
        cd_row = QtWidgets.QHBoxLayout()
        cd_lbl = QtWidgets.QLabel("카운트다운:")
        cd_lbl.setStyleSheet("color:#888; font-size:12px;")
        cd_row.addWidget(cd_lbl)
        cd_row.addStretch()
        cd_row.addWidget(self.countdown_spin)
        right.addLayout(cd_row)

        right.addWidget(self.count_label)

        # 버튼 2×2 그리드
        btn_grid = QtWidgets.QGridLayout()
        btn_grid.setSpacing(8)
        btn_grid.addWidget(self.snap_btn,            0, 0)
        btn_grid.addWidget(self.reset_btn,           0, 1)
        btn_grid.addWidget(self.print_btn,           1, 0)
        btn_grid.addWidget(self.refresh_printer_btn, 1, 1)
        right.addLayout(btn_grid)

        # 구분선
        def _sep():
            f = QtWidgets.QFrame()
            f.setFrameShape(QtWidgets.QFrame.HLine)
            f.setStyleSheet("color:#2a3a5e; margin:2px 0;")
            return f

        right.addWidget(_sep())

        # 설정 영역
        msg_lbl = QtWidgets.QLabel("영수증 문구")
        msg_lbl.setStyleSheet("color:#6a7a9a; font-size:11px;")
        right.addWidget(msg_lbl)
        right.addWidget(self.short_edit)

        logo_lbl = QtWidgets.QLabel("로고 파일")
        logo_lbl.setStyleSheet("color:#6a7a9a; font-size:11px;")
        right.addWidget(logo_lbl)
        logo_row = QtWidgets.QHBoxLayout()
        logo_row.addWidget(self.logo_edit)
        logo_row.addWidget(self.logo_btn)
        right.addLayout(logo_row)

        printer_row = QtWidgets.QHBoxLayout()
        printer_row.addWidget(self.chk_printer)
        printer_row.addStretch()
        copies_lbl = QtWidgets.QLabel("매수:")
        copies_lbl.setStyleSheet("color:#888; font-size:12px;")
        printer_row.addWidget(copies_lbl)
        printer_row.addWidget(self.copies_combo)
        right.addLayout(printer_row)
        right.addWidget(self.chk_auto_reset)

        # 프린터 포트
        port_row = QtWidgets.QHBoxLayout()
        port_lbl = QtWidgets.QLabel("포트:")
        port_lbl.setStyleSheet("color:#888; font-size:12px;")
        port_row.addWidget(port_lbl)
        port_row.addWidget(self.printer_port_combo, 1)
        right.addLayout(port_row)

        right.addWidget(self.status)

        # ════════════════════════════════════════
        # 왼쪽: 카메라(위) + 썸네일(아래)
        # ════════════════════════════════════════
        thumb_row = QtWidgets.QWidget()
        thumb_row.setFixedHeight(160)
        thumb_row_layout = QtWidgets.QHBoxLayout(thumb_row)
        thumb_row_layout.setContentsMargins(0, 0, 0, 0)
        thumb_row_layout.setSpacing(8)
        for lbl in self.thumb_labels:
            thumb_row_layout.addWidget(lbl, 1)

        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(self.video_container, 1)
        left_layout.addWidget(thumb_row)

        # ════════════════════════════════════════
        # 루트 레이아웃
        # ════════════════════════════════════════
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(14)
        root.addWidget(left_widget, 1)

        right_widget = QtWidgets.QWidget()
        right_widget.setLayout(right)
        right_widget.setFixedWidth(320)
        right_widget.setStyleSheet(
            "QWidget { background:#141428; border-radius:14px; }"
        )
        root.addWidget(right_widget, 0)

        # ── 이벤트 ──
        self.device_combo.activated.connect(self._change_device)
        self.snap_btn.clicked.connect(self._start_countdown)
        self.print_btn.clicked.connect(self._print_both)
        self.reset_btn.clicked.connect(self._reset_all)
        self.logo_btn.clicked.connect(self._choose_logo)
        self.refresh_printer_btn.clicked.connect(self._refresh_printer_ports)
        QtGui.QShortcut(QtGui.QKeySequence("Space"), self, activated=self._start_countdown)

        # ── 카메라 시작 ──
        found = self._scan_0_1()
        if found:
            default = 1 if 1 in found else 0
            self.device_combo.setCurrentText(str(default))
            self._open_cap(default)
        else:
            self._set_status("사용 가능한 카메라 없음", err=True)

    # ── 프린터 포트 새로고침 ──
    def _refresh_printer_ports(self):
        self.printer_port_combo.clear()
        self.printer_port_combo.addItem("자동 탐색", userData=None)
        ports = list_usb_candidate_ports()
        for p in ports:
            self.printer_port_combo.addItem(p, userData=p)
        if ports:
            self._set_status(f"프린터 포트 발견: {ports}")
        else:
            self._set_status("연결된 프린터 포트 없음", err=True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.countdown.setGeometry(0, 0, self.video.width(), self.video.height())
        self.flash_overlay.setGeometry(0, 0, self.video.width(), self.video.height())

    # ── 카메라 ──
    def _scan_0_1(self):
        self.device_combo.clear()
        found = []
        for i in (0, 1):
            cap = open_capture(i); ok, _ = cap.read(); cap.release()
            if ok: found.append(i)
        for i in (found if found else [0]):
            self.device_combo.addItem(str(i))
        self._set_status(f"카메라 검색 완료: {found}" if found else "카메라 없음")
        return found

    def _change_device(self, _):
        try: idx = int(self.device_combo.currentText())
        except ValueError: idx = 0
        self._open_cap(idx)

    def _open_cap(self, idx: int):
        if self.cap:
            self.timer.stop(); self.cap.release(); self.cap = None
        self.cap = open_capture(idx)
        ok, _ = self.cap.read()
        if not ok:
            self.cap.release(); self.cap = None
            self._set_status(f"장치 {idx} 열기 실패", err=True); return
        self.timer.start(33)
        self._set_status(f"장치 {idx} 연결됨  ·  Space 또는 촬영 버튼")

    def _tick(self):
        if not self.cap: return
        ok, frame = self.cap.read()
        if not ok:
            self.timer.stop()
            self._set_status("카메라 연결 끊어짐", err=True); return
        if self.mirror: frame = cv2.flip(frame, 1)
        self.last_frame = frame
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QtGui.QImage(rgb.data, w, h, ch * w, QtGui.QImage.Format.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(qimg).scaled(
            self.video.width(), self.video.height(),
            QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.video.setPixmap(pix)
        self.countdown.setGeometry(0, 0, self.video.width(), self.video.height())
        self.flash_overlay.setGeometry(0, 0, self.video.width(), self.video.height())

    # ── 카운트다운 / 촬영 ──
    def _start_countdown(self):
        if self.last_frame is None:
            self._set_status("프레임 없음", err=True); return
        if len(self.captured_images) >= self.max_shots:
            self._set_status("이미 2장 촬영됨. 초기화 후 다시 찍으세요.", err=True); return
        if self._counting_down: return
        self._counting_down = True
        self.snap_btn.setEnabled(False)
        sec = self.countdown_spin.value()
        if sec == 0: self._do_capture()
        else: self.countdown.start(sec)

    def _do_capture(self):
        self._counting_down = False
        if self.last_frame is None:
            self.snap_btn.setEnabled(True); return
        self.flash_overlay.flash()
        ts   = time.strftime("%Y%m%d_%H%M")
        path = self.captures_dir / f"photo_{ts}_{len(self.captured_images)+1:02d}.png"
        if cv2.imwrite(str(path), self.last_frame):
            self.captured_images.append((path, self.last_frame.copy()))
            self._update_thumbs()
            remain = self.max_shots - len(self.captured_images)
            self.count_label.setText(f"남은 촬영: {remain}장")
            if remain == 0:
                self.print_btn.setEnabled(True)
                self._set_status("2장 촬영 완료! 출력 버튼을 누르세요.")
            else:
                self._set_status(f"저장됨: {path.name}")
        else:
            self._set_status("저장 실패", err=True)
        if len(self.captured_images) < self.max_shots:
            self.snap_btn.setEnabled(True)

    def _update_thumbs(self):
        for i, lbl in enumerate(self.thumb_labels):
            if i < len(self.captured_images):
                frame = self.captured_images[i][1]
                rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                qimg = QtGui.QImage(rgb.data, w, h, ch * w, QtGui.QImage.Format.Format_RGB888)
                tw = max(lbl.width(),  100)
                th = max(lbl.height(), 100)
                pix = QtGui.QPixmap.fromImage(qimg).scaled(
                    tw, th, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                lbl.setPixmap(pix)
                lbl.setText("")
                lbl.setStyleSheet(
                    "background:#0a0a18; border:2px solid #e84060; border-radius:8px;")
            else:
                lbl.clear(); lbl.setText(f"사진 {i+1}")
                lbl.setStyleSheet(
                    "background:#0a0a18; border:2px dashed #2a3a5e;"
                    "border-radius:8px; color:#3a4a6e; font-size:14px;")

    def _choose_logo(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "로고 선택", os.getcwd(), "Images (*.png *.jpg *.jpeg *.bmp)")
        if path: self.logo_edit.setText(path)

    # ── 출력 ──
    def _print_both(self):
        if len(self.captured_images) < self.max_shots:
            self._set_status(f"사진을 {self.max_shots}장 모두 촬영하세요.", err=True); return

        QtGui.QGuiApplication.inputMethod().commit()
        QtWidgets.QApplication.processEvents()

        short_txt = self.short_edit.toPlainText().strip() or DEFAULT_SHORT_TEXT

        logo_path = self.logo_edit.text().strip() or DEFAULT_LOGO_PATH
        lp = Path(logo_path)
        if not lp.is_absolute(): lp = self.base_dir / lp
        if not lp.exists():
            self._set_status(f"로고 파일 없음: {lp}", err=True); return

        photos_pil = []
        for _, bgr in self.captured_images[:2]:
            photos_pil.append(Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)))

        self._set_status("합성 중...")
        QtWidgets.QApplication.processEvents()
        try:
            receipt = compose_receipt_two_photos(
                photos_pil=photos_pil,
                paper_width=PAPER_WIDTH, margin=DEFAULT_MARGIN,
                gap=DEFAULT_GAP, photo_gap=DEFAULT_PHOTO_GAP,
                letterbox_pad=DEFAULT_LETTERBOX, logo_path=str(lp),
                logo_max_h=DEFAULT_LOGO_MAX_H, receipt_text=short_txt,
                font_path=DEFAULT_FONT_PATH, date_text=time.strftime("%Y.%m.%d"),
            )
        except Exception as e:
            self._set_status(f"합성 실패: {e}", err=True); return

        ts       = time.strftime("%Y%m%d_%H%M")
        out_path = self.captures_dir / f"RECEIPT_{ts}.png"
        try:
            receipt.save(out_path)
        except Exception as e:
            self._set_status(f"저장 실패: {e}", err=True); return
        self._set_status(f"저장됨: {out_path.name}")

        success_cnt, copies = 0, 1
        if self.chk_printer.isChecked():
            copies   = int(self.copies_combo.currentText())
            # 선택된 포트 (None이면 자동탐색)
            sel_port = self.printer_port_combo.currentData()
            last_msg = ""
            self._set_status(f"출력 중... (0/{copies})")
            QtWidgets.QApplication.processEvents()
            for i in range(copies):
                ok, msg = print_image_usb(str(out_path),
                                          device=sel_port,
                                          paper_width_px=PAPER_WIDTH)
                last_msg = msg
                if ok:
                    success_cnt += 1
                    self._set_status(f"출력 중... ({success_cnt}/{copies})")
                    QtWidgets.QApplication.processEvents()
                else:
                    self._set_status(f"{i+1}번째 실패: {msg}", err=True)
                    break
            if success_cnt == copies:
                self._set_status(f"출력 완료 ({success_cnt}장)")
            else:
                self._set_status(f"일부 실패 ({success_cnt}/{copies}) | {last_msg}", err=True)

        if self.chk_auto_reset.isChecked():
            printed_ok = (not self.chk_printer.isChecked()) or (success_cnt == copies)
            if printed_ok:
                QtCore.QTimer.singleShot(800, self._reset_all)

    def _reset_all(self):
        self.captured_images.clear()
        self.snap_btn.setEnabled(True)
        self.print_btn.setEnabled(False)
        self.count_label.setText(f"남은 촬영: {self.max_shots}장")
        self._update_thumbs()
        self._set_status("초기화 완료.")

    def _set_status(self, text: str, err: bool = False):
        self.status.setText(f"{'⚠ ' if err else '✔ '}{text}")
        self.status.setStyleSheet(
            "color:#ff7070; background:#200808; border-radius:6px; padding:6px 10px; font-size:12px;"
            if err else
            "color:#4da6ff; background:#081828; border-radius:6px; padding:6px 10px; font-size:12px;"
        )

    def closeEvent(self, e):
        try:
            self.timer.stop()
            if self.cap: self.cap.release()
        finally:
            super().closeEvent(e)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = BoothCam()
    w.show()
    sys.exit(app.exec())
