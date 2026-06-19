#!/usr/bin/env python3
"""
GrowMate 표정 디스플레이 모듈 (3.5인치 RPi LCD, 480×320)

표정(검정 배경 + 컬러 테마) 6가지 상태:
  happy   — 노랑,  활짝 웃는 얼굴       (모든 조건 정상)
  thirsty — 주황,  혀 내밀고 + 물컵      (토양 건조)
  hot     — 빨강,  열기 물결 + 처진 눈   (고온)
  cold    — 하늘색, '><' 눈 + 고드름     (저온)
  sad     — 파랑,  눈물 한 방울         (조도 부족 / 어두움)
  sick    — 풀빛,  빙글 눈 + 물결 입     (이상 2개 이상 겹침 / 과습)

KMS/DRM 환경이라 /dev/fb1 직접 쓰기는 안 되므로, 데스크톱 세션 위에
pygame 전체화면 창으로 띄운다. 반드시 라즈베리파이 '데스크톱 터미널'에서 실행.

외부에서 사용:
  from face import update_face
  update_face({"soil": 45, "temp": 24, "humid": 58, "light": 520}, mood="happy")
"""

import os
import re
import math
import subprocess
import pygame

# ── 디스플레이 설정 ─────────────────────────────────────────────
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

WIDTH, HEIGHT = 480, 320     # LCD 해상도 (가로 모드)
FULLSCREEN = True            # 창으로 먼저 확인하려면 False
SHOW_INFO  = False           # 하단에 센서값 텍스트도 표시할지 (이미지처럼 깔끔하게 하려면 False)

# SPI LCD가 HDMI와 별개의 DRM 장치로 물려 가상 데스크톱 오른쪽(예: +1920+0)에
# 붙는 환경에서는, 전체화면이 아니라 LCD 위치에 테두리 없는 창을 올려야 한다.
# LCD_POS="x,y" 로 직접 지정하거나, 비우면 xrandr 로 480×320 출력 위치를 자동 감지.

# ── 색상 팔레트 ─────────────────────────────────────────────────
BLACK   = (0, 0, 0)
YELLOW  = (255, 211, 64)
BLUE    = (66, 153, 225)
ORANGE  = (255, 140, 50)
WHITE   = (235, 238, 245)
WATER   = (120, 200, 255)
TONGUE  = (255, 110, 120)
TEXT    = (200, 205, 215)
ICE     = (150, 220, 255)    # cold (저온) — 차가운 하늘색
HOT     = (255, 95, 60)      # hot  (고온) — 뜨거운 빨강·주황
SWEAT   = (120, 200, 255)    # 땀방울
SICK    = (150, 200, 120)    # sick (아픔) — 창백한 풀빛 녹색

MOOD_COLOR = {
    "happy":   YELLOW,
    "sad":     BLUE,
    "thirsty": ORANGE,
    "cold":    ICE,
    "hot":     HOT,
    "sick":    SICK,
}
VALID_MOODS = tuple(MOOD_COLOR.keys())

# ── 적정 범위 기본값 (백엔드 DEFAULT_PROFILE.preferences 와 동일) ──
# 표정 판단은 하드코딩이 아니라 이 prefs(서버에서 받아온 식물 프로필)로 한다.
# 서버 미연동 시 fallback 으로만 이 기본값을 쓴다.
DEFAULT_PREFS = {
    "tempMin": 18, "tempMax": 28,
    "humidityMin": 60, "humidityMax": 80,
    "soilMoistureMin": 40, "soilMoistureMax": 70,
    "lightLevel": "보통",
}
LIGHT_MIN_LUX = {"낮음": 150, "보통": 400, "높음": 900}

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


def _detect_lcd_pos():
    """LCD(480×320) 출력이 가상 데스크톱에서 차지하는 좌상단 위치(x, y)를 찾는다.
    1) 환경변수 LCD_POS="x,y" 가 있으면 그것을 사용.
    2) 없으면 xrandr 출력에서 480x320+X+Y 패턴을 찾아 위치 반환.
    3) 둘 다 실패하면 None (→ 위치 지정 없이 전체화면 fallback)."""
    env = os.environ.get("LCD_POS")
    if env:
        m = re.match(r"\s*(\d+)\s*,\s*(\d+)\s*$", env)
        if m:
            return int(m.group(1)), int(m.group(2))
    try:
        out = subprocess.check_output(["xrandr"], text=True,
                                      stderr=subprocess.DEVNULL)
        # 예: "SPI-1 connected 480x320+1920+0 (normal ..."
        for m in re.finditer(r"connected (?:primary )?(\d+)x(\d+)\+(\d+)\+(\d+)", out):
            w, h, x, y = (int(g) for g in m.groups())
            if (w, h) == (WIDTH, HEIGHT):
                return x, y
    except Exception:
        pass
    return None


def _init():
    global _screen, _font_large, _font_small
    if _screen is not None:
        return

    pos = _detect_lcd_pos()
    if pos is not None:
        # LCD 위치에 테두리 없는 창을 정확히 올린다 (HDMI와 별개 DRM 장치 대응).
        os.environ["SDL_VIDEO_WINDOW_POS"] = f"{pos[0]},{pos[1]}"

    pygame.init()

    if pos is not None:
        _screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
        print(f"[face] LCD 위치 {pos} 에 테두리 없는 창으로 표시")
    else:
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


# ── 조건 판단 (서버 미연동 시 센서 기반 로컬 fallback) ────────────
# 백엔드 determine_display_mood() 와 동일한 로직. 기준은 prefs(식물 프로필).
MOOD_DEADZONE = 0.05   # happy 여유: 경계에 둘 데드존 (범위 폭 대비)

_PROBLEM_MOOD = {        # 단일 이상 → 표정. 과습 단독도 sick / 'humid' 단독은 무시(happy).
    "dry":  "thirsty",   # 토양 건조
    "wet":  "sick",      # 과습
    "hot":  "hot",       # 고온
    "cold": "cold",      # 저온
    "dark": "sad",       # 조도 부족 (어두움)
}


def _detect_problems(data: dict, prefs: dict = None) -> list:
    """켜진 '이상 조건' 목록. 각 경계에 5% 데드존 적용."""
    p = prefs or DEFAULT_PREFS
    soil  = data.get("soil")
    temp  = data.get("temp")
    humid = data.get("humid")
    light = data.get("light")
    min_lux = LIGHT_MIN_LUX.get(p.get("lightLevel", "보통"), 400)
    problems = []

    if soil is not None:
        m = (p["soilMoistureMax"] - p["soilMoistureMin"]) * MOOD_DEADZONE
        if soil < p["soilMoistureMin"] - m:
            problems.append("dry")
        elif soil > p["soilMoistureMax"] + m:
            problems.append("wet")
    if temp is not None:
        m = (p["tempMax"] - p["tempMin"]) * MOOD_DEADZONE
        if temp > p["tempMax"] + m:
            problems.append("hot")
        elif temp < p["tempMin"] - m:
            problems.append("cold")
    if light is not None and light < min_lux * (1 - MOOD_DEADZONE):
        problems.append("dark")
    if humid is not None:
        m = (p["humidityMax"] - p["humidityMin"]) * MOOD_DEADZONE
        if not (p["humidityMin"] - m <= humid <= p["humidityMax"] + m):
            problems.append("humid")

    return problems


def _determine_mood(data: dict, prefs: dict = None) -> str:
    """이상 2개 이상 → sick / 1개 → 해당 표정(습도 단독 무시) / 0개 → happy."""
    problems = _detect_problems(data, prefs)
    if len(problems) >= 2:
        return "sick"
    if len(problems) == 1:
        return _PROBLEM_MOOD.get(problems[0], "happy")
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
    """미니멀 물컵 (위 넓은 사다리꼴 외곽선 + 물 + 수면선)."""
    top_l = (x, y)
    top_r = (x + w, y)
    bot_l = (x + w * 0.16, y + h)
    bot_r = (x + w * 0.84, y + h)

    # 수면 높이 및 그 지점의 좌우 폭(사다리꼴 보간)
    wl = y + h * 0.40
    f = (wl - y) / h
    wl_l = (x + w * (0.16 * f), wl)
    wl_r = (x + w * (1.0 - 0.16 * f), wl)

    # 물 채움
    pygame.draw.polygon(surf, WATER, [wl_l, wl_r, bot_r, bot_l])
    # 컵 외곽선 (사다리꼴)
    pygame.draw.lines(surf, WHITE, True, [top_l, top_r, bot_r, bot_l], 4)
    # 수면선
    pygame.draw.line(surf, WHITE, wl_l, wl_r, 3)


# ── 표정 그리기 ──────────────────────────────────────────────────
def _draw_face(surf, mood: str):
    surf.fill(BLACK)
    cx, cy, r = 240, 150, 96
    eye_y = cy - 26
    eye_dx = 44
    lx, rx_ = cx - eye_dx, cx + eye_dx   # 좌/우 눈 중심 x

    # ── happy: 검은 배경 + 노란 눈·입만으로 표현 ──────────────────
    if mood == "happy":
        # 감은 웃는 눈 (⌢ 위로 볼록) — 노란색, 더 깊게 구부림
        for ex in (lx, rx_):
            _arc_curve(surf, YELLOW, (ex, eye_y + 18), 22, 24,
                       math.radians(0), math.radians(180), 7)
        # 활짝 벌린 웃는 입 = 노란 아래 반원 + 혀 (눈에 더 가깝게 위로)
        mw, mh = 96, 84
        my = cy - 6
        mrect = pygame.Rect(cx - mw // 2, my, mw, mh)
        pygame.draw.ellipse(surf, YELLOW, mrect)                            # 노란 입
        pygame.draw.rect(surf, BLACK, (cx - mw // 2, my, mw, mh // 2))      # 윗부분 잘라 아래 반원만
        pygame.draw.ellipse(surf, TONGUE,
                            (cx - 22, my + mh - 30, 44, 26))                # 혀

    # ── sad: 검은 배경 + 파란 눈·입·눈물만으로 표현 ───────────────
    elif mood == "sad":
        # 처진 슬픈 눈 (⌣ 아래로 볼록 = happy 눈의 반대)
        for ex in (lx, rx_):
            _arc_curve(surf, BLUE, (ex, eye_y - 2), 24, 18,
                       math.radians(180), math.radians(360), 7)
        # 눈물 (오른쪽 눈 바깥 아래로 흐름)
        _teardrop(surf, WATER, rx_ + 18, eye_y + 16, 16, 30)
        # 우는 입 (아래로 처진 프라운 ⌒)
        _arc_curve(surf, BLUE, (cx, cy + 56), 40, 26,
                   math.radians(0), math.radians(180), 7)

    # ── thirsty: 검은 배경 + 반쯤 감은 주황 눈 + 헥헥 혀 + 물컵 ────
    elif mood == "thirsty":
        # 반쯤 감은 졸린 눈: 주황 원 + 가로 눈꺼풀선 + 아래 반달 채움
        er = 28
        for ex in (lx, rx_):
            pygame.draw.circle(surf, ORANGE, (ex, eye_y), er, 4)          # 원 외곽
            pygame.draw.line(surf, ORANGE, (ex - er + 1, eye_y - 1),
                             (ex + er - 1, eye_y - 1), 4)                 # 가로 눈꺼풀
            pygame.draw.arc(surf, ORANGE,
                            pygame.Rect(ex - er + 4, eye_y - er + 4,
                                        2 * (er - 4), 2 * (er - 4)),
                            math.radians(200), math.radians(340), 8)     # 아래 눈동자
        # 헥헥거리는 입(가로선) + 오른쪽 아래 아치형 빨간 혀
        mx, my = cx - 4, cy + 34
        # 오른쪽 아래로 볼록한 혀 (타원 아래 반쪽)
        tw, th = 32, 26
        tl = mx + 2
        tcx = tl + tw // 2
        pygame.draw.ellipse(surf, TONGUE, (tl, my - th, tw, th * 2))     # 혀 타원
        pygame.draw.rect(surf, BLACK, (tl, my - th, tw, th))            # 윗부분 잘라 아래 아치만
        pygame.draw.line(surf, BLACK, (tcx, my), (tcx, my + 16), 3)      # 혀 중앙 줄(입에 닿게)
        pygame.draw.line(surf, ORANGE, (mx - 38, my), (mx + 42, my), 5)  # 입(가로선, 혀 덮게 넓게)
        # 오른쪽 물컵 (작게, 입 쪽에 가깝게)
        _water_glass(surf, 300, 170, 40, 58)

    # ── cold: 검은 배경 + 하늘색 '><' 눈 + 이 악문 입 + 땀 + 눈송이 + 고드름 ──
    elif mood == "cold":
        # 꽉 감은 '><' 눈 (안쪽으로 모인 꼭짓점)
        _thick_line(surf, ICE, (lx + 14, eye_y), (lx - 18, eye_y - 16), 8)   # '>' 위팔
        _thick_line(surf, ICE, (lx + 14, eye_y), (lx - 18, eye_y + 16), 8)   # '>' 아래팔
        _thick_line(surf, ICE, (rx_ - 14, eye_y), (rx_ + 18, eye_y - 16), 8)  # '<' 위팔
        _thick_line(surf, ICE, (rx_ - 14, eye_y), (rx_ + 18, eye_y + 16), 8)  # '<' 아래팔
        # 이 악문 입 (사각 + 이빨 격자) — 눈에 더 가깝게 위로
        mw2, mh2 = 92, 34
        ml, mt = cx - mw2 // 2, cy + 14
        pygame.draw.rect(surf, ICE, (ml, mt, mw2, mh2), 5, border_radius=6)
        pygame.draw.line(surf, ICE, (ml, mt + mh2 // 2), (ml + mw2, mt + mh2 // 2), 4)  # 윗니/아랫니 경계
        for i in range(1, 6):
            vx = ml + i * mw2 // 6
            pygame.draw.line(surf, ICE, (vx, mt + 2), (vx, mt + mh2 - 2), 3)            # 이 경계(세로)
        # 입에 붙은 고드름 (이빨 바로 아래) — 입 폭 안쪽, 간격·길이 불규칙
        top = mt + mh2 - 2
        for dx, ln, hw in ((-38, 15, 6), (-26, 26, 5), (-15, 18, 5), (-3, 30, 6),
                           (10, 21, 5), (23, 28, 5), (36, 14, 4)):
            ix = cx + dx
            pygame.draw.polygon(surf, ICE, [(ix - hw, top), (ix + hw, top), (ix, top + ln)])
        # 날리는 땀방울 (얼굴 밖)
        for sx, sy, w, h in ((cx + 80, cy - 54, 14, 22), (cx + 102, cy - 6, 13, 21),
                             (cx + 92, cy + 42, 12, 19), (cx - 98, cy - 26, 12, 19)):
            _teardrop(surf, ICE, sx, sy, w, h)
        # 눈송이 (머리 위)
        for sx, sy, s in ((cx - 80, cy - 66, 14), (cx - 34, cy - 92, 11), (cx + 62, cy - 84, 12)):
            for ang in (0, 60, 120):
                a = math.radians(ang)
                dx, dy = int(s * math.cos(a)), int(s * math.sin(a))
                pygame.draw.line(surf, ICE, (sx - dx, sy - dy), (sx + dx, sy + dy), 3)

    # ── hot: 검은 배경 + 주황, 열기 물결 + 축 처진 눈 + 괴로운 입 ──
    elif mood == "hot":
        ey = cy - 8    # 눈 기준 높이 (열기 물결을 위에 둘 공간 확보)
        # 위로 피어오르는 열기 물결 3개
        for bx in (cx - 42, cx, cx + 42):
            pts = []
            for i in range(33):
                t = i / 32
                yy = (cy - 80) - t * 48
                xx = bx + 9 * math.sin(t * 2.2 * math.pi)
                pts.append((xx, yy))
            pygame.draw.lines(surf, HOT, False, pts, 5)
        # 걱정스런 눈썹 (아래로 볼록 ⌣ + 바깥쪽으로 처진 사선)
        for ex, outer in ((lx, -1), (rx_, +1)):
            pts = []
            for i in range(21):
                t = i / 20
                ang = math.radians(200 + t * 140)          # ⌣ (아래로 볼록)
                bx_ = ex + 21 * math.cos(ang)
                by_ = (ey - 22) - 8 * math.sin(ang)
                by_ += outer * (bx_ - ex) * 0.4            # 바깥쪽으로 갈수록 처짐
                pts.append((bx_, by_))
            pygame.draw.lines(surf, HOT, False, pts, 5)
            for p in (pts[0], pts[-1]):
                pygame.draw.circle(surf, HOT, (int(p[0]), int(p[1])), 2)
        # 지친 감은 눈 (아래로 볼록 ⌣) — 넓게 아래
        for ex in (lx, rx_):
            _arc_curve(surf, HOT, (ex, ey + 12), 26, 12,
                       math.radians(195), math.radians(345), 6)
        # 괴로운 입 — 강낭콩 모양 (가로로 넓고 아래 가운데가 오목)
        mw3, mh3 = 96, 48
        mtop = cy + 32
        pygame.draw.ellipse(surf, HOT, (cx - mw3 // 2, mtop, mw3, mh3))   # 채운 몸통
        # 아래 가운데 완만한 오목 — 넓고 얕게 깎아 부드러운 곡선
        pygame.draw.ellipse(surf, BLACK, (cx - 42, mtop + mh3 - 10, 84, 26))

    # ── sick: 창백한 녹색 + 빙글 도는 눈 + 메스꺼운 물결 입 + 식은땀 ──
    elif mood == "sick":
        # 어질어질 빙글 도는 눈 (나선)
        for ex in (lx, rx_):
            pts = []
            steps = 60
            for i in range(steps + 1):
                t = i / steps
                ang = t * 2.4 * 2 * math.pi      # 2.4바퀴
                rad = 3 + t * 17
                pts.append((ex + rad * math.cos(ang), eye_y + rad * math.sin(ang)))
            pygame.draw.lines(surf, SICK, False, pts, 4)
        # 메스꺼운 물결 입 (~~~)
        mw, my = 96, cy + 44
        pts = []
        for i in range(33):
            t = i / 32
            xx = cx - mw / 2 + t * mw
            yy = my + 9 * math.sin(t * 3 * math.pi)
            pts.append((xx, yy))
        pygame.draw.lines(surf, SICK, False, pts, 6)
        # 식은땀 한 방울 (왼쪽 관자놀이)
        _teardrop(surf, SWEAT, lx - 30, eye_y - 22, 12, 20)


# ── 센서값 텍스트 (옵션) ─────────────────────────────────────────
def _draw_info(surf, data: dict, mood: str):
    label = {
        "happy":   "건강해요 :)",
        "thirsty": "물이 필요해요",
        "sad":     "빛이 필요해요",
        "cold":    "너무 추워요",
        "hot":     "너무 더워요",
        "sick":    "여기저기 안 좋아요",
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
def update_face(data: dict, mood: str = None, prefs: dict = None):
    """
    센서 dict 를 받아 화면을 갱신한다.
    mood 를 직접 넘기면 그 표정을 우선(서버가 계산한 센서 표정),
    없으면 prefs(식물 프로필) 기준으로 로컬 판단.
    """
    global _current_mood
    _init()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            return

    resolved = mood if mood in VALID_MOODS else _determine_mood(data, prefs)
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
