#!/usr/bin/env python3
"""
GrowMate 라즈베리파이 → 노트북 서버 센서 전송기.
주기적으로 센서값을 읽어 노트북 FastAPI 서버로 POST 하고,
동시에 3.5인치 LCD 패널에 표정을 표시한다.

준비:  pip install requests pygame
실행:  python3 send_sensors.py
"""
import time
import random
import requests

# ── 표정 디스플레이 연결 ─────────────────────────────────────────
# face.py 가 같은 폴더에 있어야 한다.
# LCD 없이 테스트하려면 FACE_ENABLED = False 로 변경.
FACE_ENABLED = True
if FACE_ENABLED:
    try:
        from face import update_face, close as face_close
    except ImportError:
        print("[경고] face.py 를 찾을 수 없습니다. 표정 기능 비활성화.")
        FACE_ENABLED = False

# ── 설정 ────────────────────────────────────────────────────────
BASE_URL     = "http://172.20.10.3:8000"
SERVER_URL   = f"{BASE_URL}/api/sensors"
MOOD_URL     = f"{BASE_URL}/api/mood"
INTERVAL_SEC = 5       # 몇 초마다 보낼지
TEST_MODE    = True    # True: 가짜 값. 실제 센서 연결 후 False.

_last_mood = None   # 마지막으로 받은 LLM mood (서버 연결 실패 시 유지)


def read_sensors():
    """전송할 센서값 dict 를 반환한다. (반드시 '숫자'만)"""
    if TEST_MODE:
        return {
            "soil":  random.randint(15, 70),
            "temp":  round(random.uniform(20, 35), 1),
            "humid": random.randint(30, 70),
            "light": random.randint(100, 900),
        }

    # ── 실제 센서 (TEST_MODE = False 일 때 여기를 채운다) ──────────
    # import board, adafruit_dht, busio, digitalio
    # from adafruit_mcp3xxx.mcp3008 import MCP3008
    # from adafruit_mcp3xxx.analog_in import AnalogIn
    # dht = adafruit_dht.DHT11(board.D4)
    # spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
    # cs  = digitalio.DigitalInOut(board.D5)
    # mcp = MCP3008(spi, cs)
    # soil_raw  = AnalogIn(mcp, 0).value
    # light_raw = AnalogIn(mcp, 1).value
    # return {
    #     "soil":  round((1 - soil_raw / 65535) * 100),
    #     "temp":  round(dht.temperature, 1),
    #     "humid": round(dht.humidity),
    #     "light": round(light_raw / 65535 * 1000),
    # }
    raise NotImplementedError("실제 센서 코드를 채운 뒤 TEST_MODE = False 로 바꾸세요.")


def fetch_llm_mood() -> str | None:
    """백엔드에서 현재 LLM mood 를 가져온다. 실패 시 None 반환."""
    try:
        r = requests.get(MOOD_URL, timeout=3)
        if r.status_code == 200:
            return r.json().get("mood")
    except Exception:
        pass
    return None


def main():
    global _last_mood
    print(f"[GrowMate] 시작 → {SERVER_URL} "
          f"(간격 {INTERVAL_SEC}s | TEST_MODE={TEST_MODE} | FACE={FACE_ENABLED})")
    try:
        while True:
            try:
                data = read_sensors()

                # 1) LLM mood 폴링 (성공 시 갱신, 실패 시 이전 값 유지)
                fetched = fetch_llm_mood()
                if fetched:
                    _last_mood = fetched

                # 2) 표정 업데이트 — LLM mood 우선, 없으면 센서 기반
                if FACE_ENABLED:
                    update_face(data, mood=_last_mood)

                # 3) 서버 전송
                r = requests.post(SERVER_URL, json=data, timeout=5)
                print("보냄", data, "| mood:", _last_mood, "->", r.status_code)

            except requests.exceptions.ConnectionError:
                print("[경고] 서버 연결 실패 — 센서 기반 표정으로 fallback.")
                if FACE_ENABLED:
                    update_face(
                        data if 'data' in dir() else
                        {"soil": 50, "temp": 25, "humid": 55, "light": 500},
                        mood=None,  # 서버 없으면 센서 기반
                    )
            except Exception as e:
                print("오류:", e)

            time.sleep(INTERVAL_SEC)

    except KeyboardInterrupt:
        print("\n[GrowMate] 종료")
    finally:
        if FACE_ENABLED:
            face_close()


if __name__ == "__main__":
    main()
