# printer_io.py — ESC/POS USB 프린터 범용 출력
# 지원: CDC-ACM 시리얼, GS v 0 래스터, ESC * 비트이미지, 다중 baudrate 자동 시도
from __future__ import annotations
from typing import Tuple, Optional, List
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import glob, os, time

HAVE_PYSERIAL = False
Serial     = None
list_ports = None
try:
    from serial import Serial as _Serial
    from serial.tools import list_ports as _list_ports
    Serial     = _Serial
    list_ports = _list_ports
    HAVE_PYSERIAL = True
except Exception:
    pass

# ESC/POS 프린터가 공통으로 시도할 baudrate 목록 (빠른 것 먼저)
_BAUDRATES = [115200, 38400, 19200, 9600]


# =============================================================
# 이미지 전처리
# =============================================================
def _gamma_lut(gamma: float) -> list[int]:
    gamma = max(0.1, float(gamma))
    return [min(255, max(0, int(((i / 255.0) ** (1.0 / gamma)) * 255 + 0.5)))
            for i in range(256)]


def _ensure_multiple_of_8(w: int) -> int:
    return (w // 8) * 8


def _prep_image_1bpp(
    im: Image.Image, target_width: int, *,
    profile: str = "photo",
    autocontrast_cutoff: int = 2,
    gamma: float = 0.90,
    sharpness: float = 1.35,
    unsharp_radius: float = 1.0,
    unsharp_percent: int = 120,
    unsharp_threshold: int = 3,
    contrast: float = 1.08,
    brightness: float = 1.00,
    ordered_dither: bool = False,
    threshold: int = 160,
) -> Image.Image:
    g = im.convert("L")
    if target_width:
        tw = _ensure_multiple_of_8(int(target_width))
        if g.width != tw:
            g = g.resize((tw, max(1, int(g.height * tw / g.width))), Image.LANCZOS)
    if autocontrast_cutoff > 0:
        g = ImageOps.autocontrast(g, cutoff=int(autocontrast_cutoff))
    if abs(gamma - 1.0) > 1e-3:
        g = g.point(_gamma_lut(gamma))
    if abs(contrast - 1.0) > 1e-3:
        g = ImageEnhance.Contrast(g).enhance(float(contrast))
    if abs(brightness - 1.0) > 1e-3:
        g = ImageEnhance.Brightness(g).enhance(float(brightness))
    if unsharp_percent > 0 and unsharp_radius > 0:
        g = g.filter(ImageFilter.UnsharpMask(
            radius=float(unsharp_radius),
            percent=int(unsharp_percent),
            threshold=int(unsharp_threshold),
        ))
    if abs(sharpness - 1.0) > 1e-3:
        g = ImageEnhance.Sharpness(g).enhance(float(sharpness))
    if profile == "photo":
        if ordered_dither:
            return g.convert("1", dither=Image.Dither.ORDERED)
        return g.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
    t = max(0, min(255, int(threshold)))
    return g.point(lambda x: 0 if x < t else 255, mode="1")


# =============================================================
# ESC/POS 인코딩 — GS v 0 (래스터, 대부분 프린터 지원)
# =============================================================
def _encode_raster(bw: Image.Image) -> bytes:
    width, height = bw.size
    row_bytes = (width + 7) // 8
    data = bytearray(row_bytes * height)
    px = bw.load()
    idx = 0
    for y in range(height):
        byte, bit = 0, 0
        for x in range(width):
            is_black = 1 if px[x, y] == 0 else 0
            byte = (byte << 1) | is_black
            bit += 1
            if bit == 8:
                data[idx] = byte; idx += 1
                byte, bit = 0, 0
        if bit:
            byte <<= (8 - bit); data[idx] = byte; idx += 1
    xL = row_bytes & 0xFF;  xH = (row_bytes >> 8) & 0xFF
    yL = height    & 0xFF;  yH = (height    >> 8) & 0xFF
    return bytes([0x1D, 0x76, 0x30, 0x00, xL, xH, yL, yH]) + bytes(data)


# =============================================================
# ESC/POS 인코딩 — ESC * (비트이미지, 오래된 프린터 호환)
# =============================================================
def _encode_esc_star(bw: Image.Image) -> bytes:
    """
    ESC * m nL nH data  (m=33: 24-dot double density)
    24줄씩 잘라 전송 → 거의 모든 ESC/POS 기기에서 동작.
    """
    width, height = bw.size
    px     = bw.load()
    result = bytearray()
    result += b"\x1B\x33\x00"   # ESC 3 0 → 줄간격 0 (이미지 사이 틈 없애기)

    for y_base in range(0, height, 24):
        # ESC * 33 nL nH
        nL = width & 0xFF
        nH = (width >> 8) & 0xFF
        result += bytes([0x1B, 0x2A, 33, nL, nH])
        for x in range(width):
            for byte_idx in range(3):       # 3바이트 = 24도트
                byte = 0
                for bit in range(8):
                    y = y_base + byte_idx * 8 + bit
                    if y < height and px[x, y] == 0:
                        byte |= (1 << (7 - bit))
                result.append(byte)
        result += b"\x0A"                   # LF (다음 줄)

    result += b"\x1B\x32"                  # ESC 2 → 줄간격 기본값 복구
    return bytes(result)


# =============================================================
# 포트 탐색
# =============================================================
def list_usb_candidate_ports() -> List[str]:
    ports: List[str] = []
    if HAVE_PYSERIAL and list_ports:
        try:
            ports = [p.device for p in list_ports.comports() if p.device]
        except Exception:
            ports = []
    if not ports:
        ports += glob.glob("/dev/tty.usbmodem*")
        ports += glob.glob("/dev/tty.usbserial*")
        ports += glob.glob("/dev/ttyUSB*")
        ports += glob.glob("/dev/ttyACM*")
        if os.name == "nt":
            # Windows COM 포트는 pyserial로만 탐색 가능
            pass
    seen: set = set()
    return [p for p in ports if not (p in seen or seen.add(p))]  # type: ignore[func-returns-value]


# =============================================================
# 시리얼 전송
# =============================================================
def _write_chunked(ser, data: bytes, chunk: int = 2048) -> None:
    for i in range(0, len(data), chunk):
        ser.write(data[i:i + chunk])
        ser.flush()


def _try_open_serial(dev: str, baudrate: int):
    """Serial 열기. timeout/write_timeout 모두 설정."""
    return Serial(dev, baudrate=baudrate, timeout=3, write_timeout=5,
                  xonxoff=False, rtscts=False, dsrdtr=False)


# =============================================================
# 메인 출력 함수
# =============================================================
def print_image_usb(
    image_path: str,
    device: Optional[str] = None,
    baudrate: int = 0,               # 0 = 자동 시도
    paper_width_px: int = 576,
    do_cut: bool = True,
    feed_after: int = 3,
    *,
    profile: str = "photo",
    autocontrast_cutoff: int = 2,
    gamma: float = 0.90,
    sharpness: float = 1.35,
    unsharp_radius: float = 1.0,
    unsharp_percent: int = 120,
    unsharp_threshold: int = 3,
    contrast: float = 1.08,
    brightness: float = 1.00,
    ordered_dither: bool = False,
    threshold: int = 160,
) -> Tuple[bool, str]:
    """
    ESC/POS USB 프린터로 이미지 출력.
    - 포트 자동탐색 (모든 후보 순서대로 시도)
    - baudrate 자동 시도 (115200 → 38400 → 19200 → 9600)
    - GS v 0 (래스터) 실패 시 ESC * (비트이미지) 재시도
    """
    if not HAVE_PYSERIAL or Serial is None:
        return False, "pyserial 미설치. (pip install pyserial)"

    try:
        img = Image.open(image_path)
    except Exception as e:
        return False, f"이미지 열기 실패: {e}"

    # 이미지 전처리
    try:
        bw = _prep_image_1bpp(
            img, paper_width_px,
            profile=profile,
            autocontrast_cutoff=autocontrast_cutoff,
            gamma=gamma, sharpness=sharpness,
            unsharp_radius=unsharp_radius,
            unsharp_percent=unsharp_percent,
            unsharp_threshold=unsharp_threshold,
            contrast=contrast, brightness=brightness,
            ordered_dither=ordered_dither, threshold=threshold,
        )
        raster_data   = _encode_raster(bw)
        esc_star_data = _encode_esc_star(bw)
    except Exception as e:
        return False, f"이미지 변환 실패: {e}"

    # 포트 목록 결정
    env_dev  = os.environ.get("PRINTER_DEVICE")
    env_baud = os.environ.get("PRINTER_BAUDRATE")
    if env_baud:
        try: baudrate = int(env_baud)
        except ValueError: pass

    dev = device or env_dev
    if dev:
        candidates = [dev]
    else:
        candidates = list_usb_candidate_ports()
        if not candidates:
            return False, "USB 프린터 포트를 찾지 못했습니다."

    # baudrate 목록
    bauds = [baudrate] if baudrate > 0 else _BAUDRATES

    last_err = "알 수 없는 오류"

    for port in candidates:
        for baud in bauds:
            try:
                with _try_open_serial(port, baud) as ser:
                    # ── 초기화 ──
                    ser.write(b"\x1B\x40")       # ESC @  (init)
                    ser.write(b"\x1B\x61\x01")   # ESC a 1 (가운데 정렬)
                    ser.flush()
                    time.sleep(0.05)

                    # ── GS v 0 래스터 전송 시도 ──
                    try:
                        _write_chunked(ser, raster_data)
                    except Exception:
                        # 래스터 실패 → ESC * 재시도
                        ser.write(b"\x1B\x40")   # 재초기화
                        ser.flush()
                        time.sleep(0.05)
                        _write_chunked(ser, esc_star_data)

                    # ── 피드 + 컷 ──
                    if feed_after > 0:
                        ser.write(b"\x0A" * int(feed_after))
                    if do_cut:
                        ser.write(b"\x1D\x56\x42\x00")  # GS V B 0 (부분컷)
                    ser.flush()
                    time.sleep(0.1)

                return True, f"출력 완료 (port={port}, baud={baud})"

            except Exception as e:
                last_err = str(e)
                continue   # 다음 baud 또는 다음 포트 시도

    return False, f"모든 포트/baudrate 시도 실패: {last_err}"
