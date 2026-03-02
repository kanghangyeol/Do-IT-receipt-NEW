# Do-IT View (영수증 사진관)

PySide6 + OpenCV로 두 장의 사진을 찍어 영수증 형태로 합성하고(필요하면 USB 프린터 출력) 로컬에 저장하는 부스용 앱입니다. QR/웹페이지 업로드 없이 오프라인으로 동작합니다.

## 빠른 시작
- macOS/Linux  
  `git clone <repo-url> && cd doit-view`  
  **macOS는 Python 3.12 권장** → `python3.12 -m venv .venv && source .venv/bin/activate`  
  (3.13은 Qt cocoa 플러그인 문제로 실패할 수 있음)  
  `pip install --upgrade pip && pip install -r requirements.txt`  
  `cp .env.example .env` (필요한 경우만 값 설정) 후 `python app.py` 또는 `bash run_booth.sh`
- Windows (PowerShell)  
  `git clone <repo-url> ; cd doit-view`  
  `py -3 -m venv .venv ; .\.venv\Scripts\Activate.ps1`  
  `pip install --upgrade pip ; pip install -r requirements.txt`  
  `.env.example`를 `.env`로 복사 후 필요한 값만 채우고 `python app.py` 실행

## 환경변수 (.env)
- `FONT_PATH` (옵션): OS에 맞는 폰트 경로를 직접 지정할 때
- `PRINTER_DEVICE`, `PRINTER_BAUDRATE` (옵션): USB 프린터 포트/baud를 수동 지정

## 실행
- macOS/Linux: `bash run_booth.sh` (자동으로 .env 로드 및 venv 우선). 실패 시 `python app.py` 직접 실행으로 확인.
- Windows: `.venv` 활성화 후 `python app.py`.
- 사진/영수증 결과물은 `captures/`에 저장됩니다.

## 프린터 (옵션)
- `pyserial`이 requirements에 포함되어 있습니다. USB ESC/POS 프린터가 시리얼 장치로 잡히면 자동 탐색하며, 탐색 실패 시 `PRINTER_DEVICE`에 예) `COM3`(Windows) 또는 `/dev/tty.usbmodemXXXX`(macOS) 지정.
- 프린터를 쓰지 않으면 UI에서 체크를 끄면 됩니다.

## 기타
- 기본 폰트는 macOS/Windows/Linux 각각의 대표 폰트를 시도하며, 잘 안 맞으면 `.env`의 `FONT_PATH`로 지정하세요.
- `.gitignore`로 venv, 캐시, 출력물은 커밋되지 않습니다.
