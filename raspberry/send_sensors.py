#!/usr/bin/env python3
"""
GrowMate LCD 표정 표시기.
서버의 /api/display-mood 를 폴링해서 LCD에 표정을 표시한다.

준비:  pip install requests pygame
실행:  python3 send_sensors.py
"""
import time
import requests

# ── 표정 디스플레이 연결 ─────────────────────────────────────────
FACE_ENABLED = True
if FACE_ENABLED:
    try:
        from face import update_face, close as face_close
    except ImportError:
        print("[경고] face.py 를 찾을 수 없습니다. 표정 기능 비활성화.")
        FACE_ENABLED = False

# ── 설정 ────────────────────────────────────────────────────────
BASE_URL     = "http://172.20.10.6:8000"
MOOD_URL     = f"{BASE_URL}/api/display-mood"
PROFILE_URL  = f"{BASE_URL}/api/profile"
SENSORS_URL  = f"{BASE_URL}/api/sensors"
INTERVAL_SEC = 5

_last_mood = None
_prefs     = None
_last_data = {"soil": 50, "temp": 25, "humid": 55, "light": 500}


def fetch_display_mood() -> str | None:
    try:
        r = requests.get(MOOD_URL, timeout=3)
        if r.status_code == 200:
            return r.json().get("mood")
    except Exception:
        pass
    return None


def fetch_prefs() -> dict | None:
    try:
        r = requests.get(PROFILE_URL, timeout=3)
        if r.status_code == 200:
            return r.json().get("preferences")
    except Exception:
        pass
    return None


def fetch_sensors() -> dict | None:
    """서버에서 최신 센서값을 가져온다."""
    try:
        r = requests.get(SENSORS_URL, timeout=3)
        if r.status_code == 200:
            rows = r.json().get("sensors", [])
            return {s["key"]: s["value"] for s in rows}
    except Exception:
        pass
    return None


def main():
    global _last_mood, _prefs, _last_data
    print(f"[GrowMate] 시작 → {BASE_URL} (간격 {INTERVAL_SEC}s | FACE={FACE_ENABLED})")

    try:
        while True:
            try:
                fetched_prefs = fetch_prefs()
                if fetched_prefs:
                    _prefs = fetched_prefs

                fetched_sensors = fetch_sensors()
                if fetched_sensors:
                    _last_data = fetched_sensors

                fetched_mood = fetch_display_mood()
                if fetched_mood:
                    _last_mood = fetched_mood

                if FACE_ENABLED:
                    update_face(_last_data, mood=_last_mood, prefs=_prefs)

                print(
                    f"soil={_last_data.get('soil')} "
                    f"temp={_last_data.get('temp')} "
                    f"humid={_last_data.get('humid')} "
                    f"light={_last_data.get('light')} "
                    f"| mood: {_last_mood}"
                )

            except Exception as e:
                print("오류:", e)
                if FACE_ENABLED:
                    update_face(_last_data, mood=None, prefs=_prefs)

            time.sleep(INTERVAL_SEC)

    except KeyboardInterrupt:
        print("\n[GrowMate] 종료")
    finally:
        if FACE_ENABLED:
            face_close()


if __name__ == "__main__":
    main()
