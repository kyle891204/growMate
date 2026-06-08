#!/usr/bin/env python3
"""
GrowMate 표정 디스플레이 모듈
3.5인치 RPi LCD (A) v3 — SPI/fbdev 방식 (320×480)
 
표정 상태:
  happy   — 모든 조건 정상
  sad     — 토양 건조 or 습도 부족
  stressed— 온도 과열 or 조도 과강
  sleepy  — 조도 너무 낮음 (어두운 환경)
 
외부에서 사용:
  from face import update_face
  update_face({"soil": 45, "temp": 24, "humid": 58, "light": 520})
"""
 
import os
import pygame
import math
 
# ── 디스플레이 설정 ─────────────────────────────────────────────
# 라즈베리파이 OS는 KMS/DRM 으로 LCD 를 구동하므로 /dev/fb1 직접 쓰기는 안 된다.
# 데스크톱 세션 위에 pygame 창(전체화면)으로 띄운다 → LCD 에 표시됨.
# 반드시 라즈베리파이 '데스크톱의 터미널' 에서 실행할 것 (DISPLAY 가 설정돼 있어야 함).
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

WIDTH, HEIGHT = 480, 320   # 가로 모드 (LCD 해상도)

# 전체화면으로 LCD 를 꽉 채울지 여부. 창으로 먼저 확인하려면 False.
FULLSCREEN = True
 
# ── 색상 팔레트 ─────────────────────────────────────────────────
BG_HAPPY    = (220, 255, 220)   # 연두
BG_SAD      = (210, 225, 255)   # 연파랑
BG_STRESSED = (255, 220, 210)   # 연주황
BG_SLEEPY   = (235, 230, 255)   # 연보라
 
FACE_COLOR  = (255, 220, 100)   # 노란 얼굴
OUTLINE     = (60,  40,   0)
EYE_WHITE   = (255, 255, 255)
EYE_PUPIL   = (40,  30,  10)
CHEEK       = (255, 160, 130)
TEXT_COLOR  = (60,  40,   0)
PLANT_GREEN = (80, 180,  80)
 
# ── 임계값 ──────────────────────────────────────────────────────
THRESHOLDS = {
    "soil_low":    25,    # 이하 → 건조 (sad)
    "humid_low":   35,    # 이하 → 습도 부족 (sad)
    "temp_high":   30,    # 초과 → 과열 (stressed)
    "light_high":  800,   # 초과 → 강한 빛 (stressed)
    "light_low":   200,   # 이하 → 너무 어두움 (sleepy)
}
 
# ── pygame 초기화 ────────────────────────────────────────────────
_screen = None
_font_large = None
_font_small = None
_current_mood = None
 
def _init():
    global _screen, _font_large, _font_small
    if _screen is not None:
        return
    pygame.init()
    flags = pygame.FULLSCREEN if FULLSCREEN else 0
    _screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    pygame.display.set_caption("GrowMate")
    pygame.mouse.set_visible(False)
    # 한글 지원 폰트 (라즈베리파이 기본 폰트 경로)
    font_candidates = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        None,
    ]
    chosen = next((f for f in font_candidates if f and os.path.exists(f)), None)
    _font_large = pygame.font.Font(chosen, 32)
    _font_small = pygame.font.Font(chosen, 18)
 
 
# ── 조건 판단 ────────────────────────────────────────────────────
def _determine_mood(data: dict) -> str:
    soil  = data.get("soil",  50)
    temp  = data.get("temp",  25)
    humid = data.get("humid", 55)
    light = data.get("light", 500)
    t = THRESHOLDS
 
    if light <= t["light_low"]:
        return "sleepy"
    if temp > t["temp_high"] or light > t["light_high"]:
        return "stressed"
    if soil <= t["soil_low"] or humid <= t["humid_low"]:
        return "sad"
    return "happy"
 
 
# ── 도형 헬퍼 ────────────────────────────────────────────────────
def _draw_circle_aa(surf, color, pos, r, width=0):
    pygame.draw.circle(surf, color, pos, r, width)
 
def _draw_arc(surf, color, rect, start_angle, stop_angle, width=4):
    pygame.draw.arc(surf, color, rect, start_angle, stop_angle, width)
 
 
# ── 표정별 얼굴 그리기 ───────────────────────────────────────────
def _draw_face(surf, mood: str):
    cx, cy = WIDTH // 2, HEIGHT // 2 - 10
    r = 90  # 얼굴 반지름
 
    bg_map = {
        "happy":    BG_HAPPY,
        "sad":      BG_SAD,
        "stressed": BG_STRESSED,
        "sleepy":   BG_SLEEPY,
    }
    surf.fill(bg_map.get(mood, BG_HAPPY))
 
    # 얼굴 원
    _draw_circle_aa(surf, FACE_COLOR, (cx, cy), r)
    _draw_circle_aa(surf, OUTLINE,    (cx, cy), r, 3)
 
    # 눈 (공통)
    ex_off, ey_off = 30, 25  # 눈 위치 오프셋
    eye_r = 14
 
    for sign in (-1, 1):
        ex = cx + sign * ex_off
        ey = cy - ey_off
        _draw_circle_aa(surf, EYE_WHITE, (ex, ey), eye_r)
        _draw_circle_aa(surf, OUTLINE,   (ex, ey), eye_r, 2)
 
        if mood == "sleepy":
            # 반만 뜬 눈 (위쪽 절반만 칠하기)
            eyelid = pygame.Rect(ex - eye_r, ey - eye_r, eye_r * 2, eye_r)
            pygame.draw.rect(surf, bg_map["sleepy"], eyelid)
            pygame.draw.line(surf, OUTLINE,
                             (ex - eye_r, ey), (ex + eye_r, ey), 2)
            # 동공 (아래쪽)
            _draw_circle_aa(surf, EYE_PUPIL, (ex, ey + 4), 5)
        else:
            # 일반 동공
            _draw_circle_aa(surf, EYE_PUPIL, (ex + 3, ey - 3), 5)
            # 하이라이트
            _draw_circle_aa(surf, (255, 255, 255), (ex + 5, ey - 6), 2)
 
    # 입
    mouth_rect_w, mouth_rect_h = 60, 40
    mouth_x = cx - mouth_rect_w // 2
    mouth_y = cy + 20
 
    if mood == "happy":
        # 웃는 입
        _draw_arc(surf, OUTLINE,
                  pygame.Rect(mouth_x, mouth_y, mouth_rect_w, mouth_rect_h),
                  math.radians(200), math.radians(340), 4)
        # 볼터치
        for sign in (-1, 1):
            pygame.draw.ellipse(surf, CHEEK,
                                pygame.Rect(cx + sign * 52 - 14, cy + 10, 28, 16))
 
    elif mood == "sad":
        # 우는 입 (뒤집힌 호)
        _draw_arc(surf, OUTLINE,
                  pygame.Rect(mouth_x, mouth_y + 10, mouth_rect_w, mouth_rect_h),
                  math.radians(20), math.radians(160), 4)
        # 눈물
        for sign in (-1, 1):
            ex = cx + sign * ex_off
            pygame.draw.ellipse(surf, (100, 160, 255),
                                pygame.Rect(ex - 4, cy - ey_off + eye_r, 8, 14))
 
    elif mood == "stressed":
        # 일자 입
        pygame.draw.line(surf, OUTLINE,
                         (cx - 22, cy + 42), (cx + 22, cy + 42), 4)
        # 찡그린 눈썹
        for sign in (-1, 1):
            ex = cx + sign * ex_off
            ey = cy - ey_off
            bx1 = ex - 14
            bx2 = ex + 14
            by1 = ey - eye_r - 8 + sign * 6
            by2 = ey - eye_r - 8 - sign * 6
            pygame.draw.line(surf, OUTLINE, (bx1, by1), (bx2, by2), 4)
        # 땀방울
        pygame.draw.polygon(surf, (100, 200, 255), [
            (cx + r - 10, cy - 30),
            (cx + r + 4,  cy - 18),
            (cx + r - 10, cy - 10),
        ])
 
    elif mood == "sleepy":
        # 지그재그 ZZZ 폰트로
        zz = _font_large.render("z z z", True, (160, 130, 200))
        surf.blit(zz, (cx + 40, cy - r + 5))
        # 살짝 웃는 입
        _draw_arc(surf, OUTLINE,
                  pygame.Rect(mouth_x + 10, mouth_y + 5,
                               mouth_rect_w - 20, mouth_rect_h - 10),
                  math.radians(200), math.radians(340), 3)
 
    # 귀여운 잎사귀 (머리 위)
    pygame.draw.ellipse(surf, PLANT_GREEN,
                        pygame.Rect(cx - 10, cy - r - 30, 20, 30))
    pygame.draw.line(surf, PLANT_GREEN,
                     (cx, cy - r - 30), (cx, cy - r - 5), 2)
 
 
# ── 센서값 + 상태 텍스트 표시 ────────────────────────────────────
def _draw_info(surf, data: dict, mood: str):
    mood_label = {
        "happy":    "건강해요 😊",
        "sad":      "물이 필요해요 😢",
        "stressed": "너무 더워요 😰",
        "sleepy":   "빛이 필요해요 😴",
    }
    # 상태 텍스트 (상단)
    label = _font_large.render(mood_label.get(mood, ""), True, TEXT_COLOR)
    surf.blit(label, (10, 8))
 
    # 센서값 (하단)
    soil  = data.get("soil",  "-")
    temp  = data.get("temp",  "-")
    humid = data.get("humid", "-")
    light = data.get("light", "-")
 
    items = [
        f"🌱 토양 {soil}%",
        f"🌡 온도 {temp}°C",
        f"💧 습도 {humid}%",
        f"☀ 조도 {light}",
    ]
    y = HEIGHT - 26
    for i, txt in enumerate(items):
        t = _font_small.render(txt, True, TEXT_COLOR)
        surf.blit(t, (8 + i * 118, y))
 
 
# ── 공개 API ─────────────────────────────────────────────────────
def update_face(data: dict, mood: str = None):
    """
    센서 dict 를 받아 화면을 갱신한다.
    mood 를 직접 넘기면 LLM 감정 우선, 없으면 센서값으로 판단.
    send_sensors.py 에서 호출:
        from face import update_face
        update_face({"soil": 45, "temp": 24, "humid": 58, "light": 520}, mood="happy")
    """
    global _current_mood
    _init()

    # pygame 이벤트 처리 (창 종료 등)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            return

    resolved = mood if mood in ("happy", "sad", "stressed", "sleepy") else _determine_mood(data)
    if resolved != _current_mood:
        _current_mood = resolved

    _draw_face(_screen, resolved)
    _draw_info(_screen, data, resolved)
    pygame.display.flip()
 
 
def close():
    """프로그램 종료 시 pygame 정리"""
    pygame.quit()
 
 
# ── 단독 실행 테스트 ─────────────────────────────────────────────
if __name__ == "__main__":
    import time, random
    print("[face.py] 단독 테스트 실행 (Ctrl+C 로 종료)")
    moods_test = [
        {"soil": 45, "temp": 24, "humid": 58, "light": 520},  # happy
        {"soil": 20, "temp": 24, "humid": 30, "light": 500},  # sad
        {"soil": 45, "temp": 33, "humid": 55, "light": 520},  # stressed
        {"soil": 45, "temp": 24, "humid": 55, "light": 100},  # sleepy
    ]
    try:
        for d in moods_test:
            update_face(d)
            print("mood:", _determine_mood(d), d)
            time.sleep(3)
    except KeyboardInterrupt:
        pass
    finally:
        close()