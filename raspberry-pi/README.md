# GrowMate 라즈베리파이 센서 전송

라즈베리파이가 센서값을 읽어 **노트북 서버**로 보내고, 앱(홈 화면)이 그 값을 보여줍니다.

```
[라즈베리파이] --POST /api/sensors--> [노트북 FastAPI 서버] <--GET /api/sensors-- [웹앱(홈)]
```

## 1. 사전 조건

- **라즈베리파이와 노트북이 같은 Wi-Fi**에 연결돼 있어야 합니다.
- 노트북 서버가 `0.0.0.0:8000`으로 실행 중이어야 합니다(외부 접속 허용):
  ```
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
  ```
- 노트북 Wi-Fi IP: **`172.17.67.118`** (바뀌면 노트북에서 `ipconfig`로 다시 확인)

## 2. 노트북 방화벽 허용 (한 번만)

Windows 방화벽이 8000 포트 인바운드를 막을 수 있습니다. **노트북에서 관리자 PowerShell**로 한 번 실행:

```powershell
New-NetFirewallRule -DisplayName "GrowMate 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

## 3. 라즈베리파이에서 실행

```bash
pip install requests
python3 send_sensors.py
```

- 처음엔 `TEST_MODE = True`(기본)라 **배선 없이 가짜 값**을 보냅니다 → 파이프라인부터 확인하세요.
- 잘 되면 홈 화면 센서 카드 숫자가 5초마다 바뀝니다.

## 4. 연결 확인

라즈베리파이에서 서버가 보이는지 먼저 테스트:

```bash
curl http://172.17.67.118:8000/api/sensors
```
JSON이 나오면 연결 OK. `Connection refused`/타임아웃이면 → Wi-Fi 동일망 여부, 서버 `--host 0.0.0.0`, 방화벽(2번)을 점검하세요.

## 5. 실제 센서로 전환

`send_sensors.py`의 `read_sensors_real()`에 실제 센서 읽기 코드를 채운 뒤 `TEST_MODE = False`로 바꿉니다.
DHT22(온습도) + MCP3008(토양/조도 아날로그) 예시 코드가 함수 주석에 들어 있습니다.

```bash
pip install adafruit-circuitpython-dht adafruit-circuitpython-mcp3xxx
```

## 보내는 데이터 형식

```json
{ "soil": 24, "temp": 24.6, "humid": 58, "light": 520 }
```
| 키 | 의미 | 단위 | 상태 판정(서버) |
|---|---|---|---|
| `soil` | 토양 수분 | % | 30 미만 → 주의 |
| `temp` | 온도 | °C | 15~28 벗어나면 주의 |
| `humid` | 습도 | % | 40~75 벗어나면 주의 |
| `light` | 조도 | lux | 500 미만 → 주의 |

가진 센서만 보내도 됩니다(없는 키 생략 가능). 상태(good/warn) 판정과 한글 라벨은 서버·앱이 알아서 합니다.

--------------------------------------------------------

1. 배선표 (이대로 꽂으면 코드 그대로 동작)

  DHT11 (온습도)

  ┌─────────┬──────────────────┐
  │ 센서 핀 │   라즈베리파이   │
  ├─────────┼──────────────────┤
  │ VCC     │ 3.3V (물리 1번)  │
  ├─────────┼──────────────────┤
  │ DATA    │ GPIO4 (물리 7번) │
  ├─────────┼──────────────────┤
  │ GND     │ GND              │
  └─────────┴──────────────────┘

  MCP3008 (ADC) ─ SPI

  ┌────────────┬─────────────────────────┐
  │  MCP3008   │      라즈베리파이       │
  ├────────────┼─────────────────────────┤
  │ VDD, VREF  │ 3.3V                    │
  ├────────────┼─────────────────────────┤
  │ AGND, DGND │ GND                     │
  ├────────────┼─────────────────────────┤
  │ CLK        │ GPIO11 / SCLK (물리 23) │
  ├────────────┼─────────────────────────┤
  │ DOUT       │ GPIO9 / MISO (물리 21)  │
  ├────────────┼─────────────────────────┤
  │ DIN        │ GPIO10 / MOSI (물리 19) │
  ├────────────┼─────────────────────────┤
  │ CS/SHDN    │ GPIO5 (물리 29)         │
  ├────────────┼─────────────────────────┤
  │ CH0        │ ← 토양센서 AOUT         │
  └────────────┴─────────────────────────┘

  토양 정전식 센서 → VCC=3.3V(MCP 기준 초과 방지), GND=GND, AOUT→MCP3008 CH0

  BH1750 (조도) ─ I2C

  ┌────────┬────────────────┐
  │ BH1750 │  라즈베리파이  │
  ├────────┼────────────────┤
  │ VCC    │ 3.3V           │
  ├────────┼────────────────┤
  │ GND    │ GND            │
  ├────────┼────────────────┤
  │ SDA    │ GPIO2 (물리 3) │
  ├────────┼────────────────┤
  │ SCL    │ GPIO3 (물리 5) │
  └────────┴────────────────┘

  2. 라즈베리파이에서 준비 (한 번만)

  # SPI · I2C 켜기
  sudo raspi-config nonint do_spi 0
  sudo raspi-config nonint do_i2c 0
  sudo reboot

  # 라이브러리 설치 (재부팅 후)
  pip3 install adafruit-circuitpython-dht adafruit-circuitpython-mcp3xxx
  adafruit-circuitpython-bh1750

  ▎ 최신 라즈비안에서 externally-managed-environment 오류가 나면 → 끝에
  ▎ --break-system-packages 붙이거나 python3 -m venv venv && source
  ▎ venv/bin/activate 후 설치.

  연결 확인(선택): i2cdetect -y 1 → 0x23 보이면 BH1750 정상 / ls
  /dev/spidev* → spidev0.0 보이면 SPI 정상.

  3. 실행 & 토양센서 보정

  python3 send_sensors.py
  콘솔에 (보정용) soil raw=##### 가 찍힙니다.
  1. 센서를 공기 중(마른 상태) 에 둔 raw → SOIL_RAW_DRY
  2. 센서를 물에 담근 raw → SOIL_RAW_WET

  이 두 값을 send_sensors.py 상단에 적어주면 토양 수분 %가 정확해집니다.
  (기본값으로도 일단 동작은 함)

  4. 마지막 체크

  - SERVER_URL의 IP(172.20.10.3)가 지금 노트북 IP와 같은지 (ipconfig로 확인)
  - 노트북 백엔드가 --host 0.0.0.0으로 떠 있고, 방화벽 8000 열려 있는지

  이제 실행하면 콘솔에 보냄 {...} -> 200 이 뜨고, 10초 안에 웹 홈 화면에
  실제 값이 반영됩니다.

  ---
  DHT11이 가끔 읽기 실패(무시)를 출력해도 정상입니다 (센서 특성상 간헐적
  실패 → 그 주기만 건너뛰고 다음에 재시도). 혹시 배선 사진을 주시면 핀이
  맞게 꽂혔는지 같이 확인해드릴게요.