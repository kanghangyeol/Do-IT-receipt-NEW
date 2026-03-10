# Do-IT View (영수증 사진관)

PySide6 + OpenCV로 두 장의 사진을 찍어 영수증 형태로 합성하고(필요하면 USB 프린터 출력) 로컬에 저장하는 부스용 앱입니다. QR/웹페이지 업로드 기능은 모두 제거되었으며 오프라인으로만 동작합니다.

## 빠른 시작

### macOS / Linux

```bash
git clone https://github.com/kanghangyeol/Do-IT-receipt-NEW.git
cd Do-IT-receipt-NEW

# 가상환경 생성 (Python 3.12 권장)
python3 -m venv .venv
source .venv/bin/activate

# 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt

# 실행
bash run_booth.sh
```

### Windows (PowerShell)

```powershell
git clone https://github.com/kanghangyeol/Do-IT-receipt-NEW.git
cd Do-IT-receipt-NEW

py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt

python app.py
```

## 실행 방법

| 방법 | 명령어 |
|------|--------|
| **권장** (macOS/Linux) | `bash run_booth.sh` |
| 직접 실행 | `python app.py` |
| 디버그 모드 | `USE_QT_DEBUG=1 bash run_booth.sh` |

- `run_booth.sh`는 venv 자동 감지, 패키지 설치 여부 확인, macOS Qt 플러그인 문제 자동 수정을 모두 처리합니다.
- 사진/영수증 결과물은 `captures/` 폴더에 저장됩니다.

## 환경변수 (.env) — 모두 선택사항

| 변수 | 설명 |
|------|------|
| `FONT_PATH` | OS 기본 폰트 대신 사용할 폰트 경로 |
| `PRINTER_DEVICE` | USB 프린터 포트 수동 지정 (예: `COM3`, `/dev/tty.usbmodemXXXX`) |
| `PRINTER_BAUDRATE` | 프린터 baudrate 수동 지정 (기본: 자동 시도) |

`.env.example`를 `.env`로 복사 후 필요한 값만 설정하세요.

## 프린터 (옵션)

USB ESC/POS 프린터가 시리얼 장치로 인식되면 자동으로 탐색합니다.

- 포트 자동 탐색 실패 시 `PRINTER_DEVICE` 환경변수로 직접 지정
- GS v 0 (래스터) 방식 우선 시도, 실패 시 ESC * (비트이미지) 방식으로 자동 전환
- 프린터를 사용하지 않으려면 UI에서 "USB 프린터 출력" 체크를 끄면 됩니다

## macOS Qt 플러그인 문제 해결

`run_booth.sh`가 실행 시 자동으로 처리하므로 별도 조치가 필요 없습니다.

문제가 지속될 경우:
1. `USE_QT_DEBUG=1 bash run_booth.sh` 로 로딩 로그 확인
2. 수동으로 플래그 제거: `find .venv -name "*.dylib" -exec chflags nohidden {} \;`

## 기타

- 기본 폰트: macOS(`AppleSDGothicNeo`), Windows(`malgun.ttf`), Linux(`DejaVuSans`). 다른 폰트를 쓰려면 `.env`의 `FONT_PATH`로 지정.
- `.gitignore`로 venv, 캐시, 출력물(`captures/`)은 커밋되지 않습니다.
