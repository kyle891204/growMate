#!/usr/bin/env python3
"""
GrowMate 표정 디스플레이 모듈 (3.5인치 RPi LCD, 480×320)

표정 초안(검정 배경 + 컬러 테마)에 맞춘 4가지 상태:
  happy   — 노랑, 활짝 웃는 얼굴      (모든 조건 정상 / 기쁨)
  thirsty — 주황, 혀 내밀고 + 물컵     (토양 건조·습도 부족 / 목마름)
  angry   — 빨강, '><' 화난 눈        (과열·과한 빛 / 화남·짜증)
  sad     — 파랑, 눈물 한 방울        (빛 부족·어두움 / 슬픔·우울)

KMS/DRM 환경이라 /dev/fb1 직접 쓰기는 안 되므로, 데스크톱 세션 위에
pygame 전체화면 창으로 띄운다. 반드시 라즈베리파이 '데스크톱 터미널'에서 실행.

외부에서 사용:
  from face import update_face
  update_face({"soil": 45, "temp": 24, "humid": 58, "light": 520}, mood="happy")
"""

import os
import math
import pygame

# ── 디스플레이 설정 ─────────────────────────────────────────────
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

WIDTH, HEIGHT = 480, 320     # LCD 해상도 (가로 모드)
FULLSCREEN = True            # 창으로 먼저 확인하려면 False
SHOW_INFO  = False           # 하단에 센서값 텍스트도 표시할지 (이미지처럼 깔끔하게 하려면 False)

# ── 색상 팔레트 ─────────────────────────────────────────────────
BLACK   = (0, 0, 0)
YELLOW  = (255, 211, 64)
BLUE    = (66, 153, 225)
ORANGE  = (255, 140, 50)
RED     = (240, 60, 55)
WHITE   = (235, 238, 245)
WATER   = (120, 200, 255)
TONGUE  = (255, 110, 120)
TEXT    = (200, 205, 215)

MOOD_COLOR = {
    "happy":   YELLOW,
    "sad":     BLUE,
    "thirsty": ORANGE,
    "angry":   RED,
}
VALID_MOODS = tuple(MOOD_COLOR.keys())

# ── 임계값 ──────────────────────────────────────────────────────
THRESHOLDS = {
    "soil_low":    25,    # 이하 → 건조 (thirsty)
    "humid_low":   35,    # 이하 → 습도 부족 (thirsty)
    "temp_high":   30,    # 초과 → 과열 (angry)
    "light_high":  800,   # 초과 → 강한 빛 (angry)
    "light_low":   200,   # 이하 → 너무 어두움 (sad)
}

# ── pygame 상태 ──────────────────────────────────────────────────
_screen = None
_font_large = None
_font_small = None
_current_mood = None


def _pick_lcd_display():
    """크기가 LCD(480×320)와 일치하는 디스플레이 인덱스를 찾는다 (없으면 0).
    환경변수 LCD_DISPLAY 로 강제 지정 가능."""
    env = os.environ.get("LCD_DISPLAY")
    if env is not None and env.isdigit():
        return int(env)
    try:
        for i, sz in enumerate(pygame.display.get_desktop_sizes()):
            if tuple(sz) == (WIDTH, HEIGHT):
                return i
    except Exception:
        pass
    return 0


def _init():
    global _screen, _font_large, _font_small
    if _screen is not None:
        return
    pygame.init()
    idx = _pick_lcd_display()
    flags = pygame.FULLSCREEN if FULLSCREEN else 0
    try:
        # pygame 2.0+ : display 인자로 특정 모니터(LCD)에 전체화면
        _screen = pygame.display.set_mode((WIDTH, HEIGHT), flags, display=idx)
    except TypeError:
        _screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    print(f"[face] display index = {idx} (전체 디스플레이: "
          f"{pygame.display.get_num_displays() if hasattr(pygame.display, 'get_num_displays') else '?'})")
    pygame.display.set_caption("GrowMate")
    pygame.mouse.set_visible(False)
    font_candidates = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        None,
    ]
    chosen = next((f for f in font_candidates if f and os.path.exists(f)), None)
    _font_large = pygame.font.Font(chosen, 30)
    _font_small = pygame.font.Font(chosen, 18)


# ── 조건 판단 (LLM mood 없을 때 센서 기반 fallback) ───────────────
def _determine_mood(data: dict) -> str:
    soil  = data.get("soil",  50)
    temp  = data.get("temp",  25)
    humid = data.get("humid", 55)
    light = data.get("light", 500)
    t = THRESHOLDS

    if soil <= t["soil_low"] or humid <= t["humid_low"]:
        return "thirsty"
    if temp > t["temp_high"] or light > t["light_high"]:
        return "angry"
    if light <= t["light_low"]:
        return "sad"
    return "happy"


# ── 도형 헬퍼 ────────────────────────────────────────────────────
def _arc_curve(surf, color, center, rx, ry, a0, a1, width, segments=48):
    """math 각도(반시계, 0=오른쪽)로 부드러운 타원 호를 그린다. 양끝 둥근 캡."""
    cx, cy = center
    pts = []
    for i in range(segments + 1):
        t = a0 + (a1 - a0) * i / segments
        x = cx + rx * math.cos(t)
        y = cy - ry * math.sin(t)   # 화면 y는 아래로 증가
        pts.append((x, y))
    if len(pts) >= 2:
        pygame.draw.lines(surf, color, False, pts, width)
    cap = max(1, width // 2)
    for p in (pts[0], pts[-1]):
        pygame.draw.circle(surf, color, (int(p[0]), int(p[1])), cap)


def _thick_line(surf, color, p1, p2, width):
    pygame.draw.line(surf, color, p1, p2, width)
    r = max(1, width // 2)
    pygame.draw.circle(surf, color, (int(p1[0]), int(p1[1])), r)
    pygame.draw.circle(surf, color, (int(p2[0]), int(p2[1])), r)


def _teardrop(surf, color, x, y, w, h):
    """위가 뾰족하고 아래가 둥근 물방울."""
    pygame.draw.polygon(surf, color, [
        (x, y), (x - w // 2, y + h * 0.55), (x + w // 2, y + h * 0.55),
    ])
    pygame.draw.circle(surf, color, (int(x), int(y + h * 0.6)), int(w // 2))


def _water_glass(surf, x, y, w, h):
    """오른쪽에 놓이는 물컵 아이콘 (위가 넓은 사다리꼴 + 물)."""
    top_l = (x, y)
    top_r = (x + w, y)
    bot_l = (x + w * 0.16, y + h)
    bot_r = (x + w * 0.84, y + h)
    wl = y + h * 0.34   # 수면 높이
    # 물 채움
    wl_l = (x + w * 0.07, wl)
    wl_r = (x + w * 0.93, wl)
    pygame.draw.polygon(surf, WATER, [wl_l, wl_r, bot_r, bot_l])
    # 컵 외곽선
    pygame.draw.lines(surf, WHITE, False, [top_l, bot_l, bot_r, top_r], 4)
    # 수면선
    pygame.draw.line(surf, WHITE, wl_l, wl_r, 3)


# ── 표정 그리기 ──────────────────────────────────────────────────
def _draw_face(surf, mood: str):
    surf.fill(BLACK)
    cx, cy, r = 240, 150, 96
    eye_y = cy - 26
    eye_dx = 44
    lx, rx_ = cx - eye_dx, cx + eye_dx   # 좌/우 눈 중심 x

    # ── happy: 노랑 가득 찬 얼굴 + 활짝 웃음 ──────────────────────
    if mood == "happy":
        pygame.draw.circle(surf, YELLOW, (cx, cy), r)
        # 감은 웃는 눈 (⌢ 위로 볼록)
        for ex in (lx, rx_):
            _arc_curve(surf, BLACK, (ex, eye_y + 6), 22, 16,
                       math.radians(0), math.radians(180), 7)
        # 볼터치
        for ex in (lx, rx_):
            cheek = pygame.Surface((40, 22), pygame.SRCALPHA)
            pygame.draw.ellipse(cheek, (255, 140, 120, 150), cheek.get_rect())
            surf.blit(cheek, (ex - 20, cy + 18))
        # 활짝 벌린 웃는 입 (아래 반원) + 혀
        mw, mh = 96, 84
        mrect = pygame.Rect(cx - mw // 2, cy + 6, mw, mh)
        pygame.draw.ellipse(surf, BLACK, mrect)
        pygame.draw.rect(surf, YELLOW, (cx - mw // 2, cy + 6, mw, mh // 2))  # 윗부분 가려 평평한 위쪽
        pygame.draw.line(surf, BLACK, (cx - mw // 2 + 3, cy + 6 + mh // 2),
                         (cx + mw // 2 - 3, cy + 6 + mh // 2), 6)            # 윗입술 선
        pygame.draw.ellipse(surf, TONGUE,
                            (cx - 22, cy + 6 + mh - 30, 44, 26))            # 혀

    # ── sad: 파란 외곽선 + 처진 눈 + 눈물 ────────────────────────
    elif mood == "sad":
        pygame.draw.circle(surf, BLUE, (cx, cy), r, 7)
        # 처진 슬픈 눈: 위로 볼록한 눈꺼풀(⌢) + 아래 동공, 바깥쪽이 살짝 내려감
        for ex in (lx, rx_):
            _arc_curve(surf, BLUE, (ex, eye_y + 4), 19, 13,
                       math.radians(10), math.radians(170), 6)
            pygame.draw.circle(surf, BLUE, (ex, eye_y + 8), 5)   # 동공
        # 눈물 (왼쪽 눈 아래)
        _teardrop(surf, WATER, lx, eye_y + 22, 18, 30)
        # 우는 입 (⌢ 프라운)
        _arc_curve(surf, BLUE, (cx, cy + 66), 34, 24,
                   math.radians(20), math.radians(160), 7)

    # ── thirsty: 주황 외곽선 + 혀 + 물컵 ─────────────────────────
    elif mood == "thirsty":
        pygame.draw.circle(surf, ORANGE, (cx, cy), r, 7)
        # 편안히 감은 눈 (⌣ 아래로 볼록 = 흐뭇)
        for ex in (lx, rx_):
            _arc_curve(surf, ORANGE, (ex, eye_y - 2), 20, 14,
                       math.radians(200), math.radians(340), 7)
        # 입 (벌린 윗선) + 아래로 늘어진 혀
        pygame.draw.arc(surf, ORANGE,
                        pygame.Rect(cx - 34, cy + 22, 68, 44),
                        math.radians(200), math.radians(340), 7)
        pygame.draw.ellipse(surf, TONGUE, (cx - 14, cy + 48, 28, 40))  # 늘어진 혀
        pygame.draw.line(surf, (210, 70, 90), (cx, cy + 54), (cx, cy + 82), 3)
        # 오른쪽 물컵
        _water_glass(surf, 372, 116, 74, 96)

    # ── angry: 빨강 외곽선 + '><' 눈 + 분노 마크 ─────────────────
    elif mood == "angry":
        pygame.draw.circle(surf, RED, (cx, cy), r, 7)
        # 왼쪽 눈 '>' : 오른쪽이 꼭짓점, 팔이 왼쪽으로
        _thick_line(surf, RED, (lx + 20, eye_y), (lx - 18, eye_y - 18), 8)
        _thick_line(surf, RED, (lx + 20, eye_y), (lx - 18, eye_y + 18), 8)
        # 오른쪽 눈 '<' : 왼쪽이 꼭짓점, 팔이 오른쪽으로
        _thick_line(surf, RED, (rx_ - 20, eye_y), (rx_ + 18, eye_y - 18), 8)
        _thick_line(surf, RED, (rx_ - 20, eye_y), (rx_ + 18, eye_y + 18), 8)
        # 이 악문 입 (작은 프라운)
        _arc_curve(surf, RED, (cx, cy + 64), 26, 16,
                   math.radians(20), math.radians(160), 7)
        # 분노 마크 (💢) 오른쪽 위
        mvx, mvy = cx + 78, cy - 70
        pygame.draw.line(surf, RED, (mvx - 12, mvy), (mvx + 12, mvy), 5)
        pygame.draw.line(surf, RED, (mvx, mvy - 12), (mvx, mvy + 12), 5)
        pygame.draw.line(surf, RED, (mvx - 9, mvy - 9), (mvx + 9, mvy + 9), 5)
        pygame.draw.line(surf, RED, (mvx - 9, mvy + 9), (mvx + 9, mvy - 9), 5)


# ── 센서값 텍스트 (옵션) ─────────────────────────────────────────
def _draw_info(surf, data: dict, mood: str):
    label = {
        "happy":   "건강해요 :)",
        "thirsty": "물이 필요해요",
        "angry":   "너무 더워요",
        "sad":     "빛이 필요해요",
    }
    t = _font_large.render(label.get(mood, ""), True, TEXT)
    surf.blit(t, (12, 8))

    soil  = data.get("soil",  "-")
    temp  = data.get("temp",  "-")
    humid = data.get("humid", "-")
    light = data.get("light", "-")
    items = [f"토양 {soil}%", f"온도 {temp}C", f"습도 {humid}%", f"조도 {light}"]
    y = HEIGHT - 26
    for i, txt in enumerate(items):
        s = _font_small.render(txt, True, TEXT)
        surf.blit(s, (10 + i * 118, y))


# ── 공개 API ─────────────────────────────────────────────────────
def update_face(data: dict, mood: str = None):
    """
    센서 dict 를 받아 화면을 갱신한다.
    mood 를 직접 넘기면 LLM 감정 우선, 없으면 센서값으로 판단.
    """
    global _current_mood
    _init()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            return

    resolved = mood if mood in VALID_MOODS else _determine_mood(data)
    _current_mood = resolved

    _draw_face(_screen, resolved)
    if SHOW_INFO:
        _draw_info(_screen, data, resolved)
    pygame.display.flip()


def close():
    """프로그램 종료 시 pygame 정리"""
    pygame.quit()


# ── 단독 실행 테스트 ─────────────────────────────────────────────
if __name__ == "__main__":
    import time
    print("[face.py] 단독 테스트 — 4가지 표정 순환 (Ctrl+C 종료)")
    demo = {"soil": 45, "temp": 24, "humid": 58, "light": 520}
    try:
        for m in VALID_MOODS:
            print("mood:", m)
            update_face(demo, mood=m)
            time.sleep(3)
    except KeyboardInterrupt:
        pass
    finally:
        close()
