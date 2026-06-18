"""
Growmate LLM 백엔드 (Google Gemini API)
- /api/chat: 식물 페르소나 + 센서 컨텍스트, SSE 스트리밍
- /api/health: 상태 확인
- 라즈베리파이는 이 백엔드만 띄우면 됨 (로컬 모델 X)

실행:
    uvicorn main:app --host 0.0.0.0 --port 8000
"""
import asyncio
import json
import os
import re
import threading
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# 실행 방식에 따라 import 경로가 달라진다.
#   - backend/ 에서:        uvicorn main:app          → 최상위 모듈
#   - 저장소 루트에서:       uvicorn backend.main:app  → backend 패키지의 서브모듈
# 둘 다 동작하도록 양쪽을 시도한다.
try:
    from database import Base, engine, get_db, SessionLocal
    import models  # noqa: F401 — Base.metadata 에 테이블 등록을 위해 import 필요
    from models import (
        ChatMessage, Setting, Suggestion, seed_defaults,
        Plant, PlantSpecies, WaterLog, LedLog, SensorData, SensorLatest, Alert,
        SensorHealth, DEFAULT_PLANT_ID, DEFAULT_PROFILE,
    )
except ModuleNotFoundError:
    from backend.database import Base, engine, get_db, SessionLocal
    from backend import models  # noqa: F401
    from backend.models import (
        ChatMessage, Setting, Suggestion, seed_defaults,
        Plant, PlantSpecies, WaterLog, LedLog, SensorData, SensorLatest, Alert,
        SensorHealth, DEFAULT_PLANT_ID, DEFAULT_PROFILE,
    )

load_dotenv()

# db 연동: 테이블 생성 후 기본값(설정/제안) 시드
Base.metadata.create_all(bind=engine)
seed_defaults()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("MODEL", "gemini-2.5-flash")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY 환경변수가 없음. .env를 확인하세요. "
        "키 발급: https://aistudio.google.com/apikey"
    )

client = genai.Client(api_key=GEMINI_API_KEY)

# LLM이 마지막으로 출력한 감정 태그를 메모리에 보관 (라즈베리파이 LCD 표정용)
_current_llm_mood: str = "happy"

app = FastAPI(title="Growmate LLM (Gemini)")

# 개발 편의용 CORS. 배포 시 좁힐 것.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 요청 스키마 ─────────────────────────────────────────────────
class Sensor(BaseModel):
    temp: float
    humidity: float
    soil: Optional[float] = None


class ChatTurn(BaseModel):
    from_: str = Field(..., alias="from")   # "user" | "plant"
    text: str

    class Config:
        populate_by_name = True


class PlantProfile(BaseModel):
    """사용자가 정한 식물 정체성(프론트 localStorage growmate_profile). 페르소나에 주입."""
    name: Optional[str] = None
    species: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    # 공감채팅은 센서 없이도 동작한다(감정 공감 중심). 있으면 페르소나에 컨디션 반영.
    sensor: Optional[Sensor] = None
    history: List[ChatTurn] = []
    # 식물 이름/종 → 식물이 자기 이름을 알도록 system prompt 에 반영
    profile: Optional[PlantProfile] = None


# ── 식물 페르소나 system prompt ────────────────────────────────
def build_system_prompt(s: Optional[Sensor], profile: Optional[PlantProfile] = None) -> str:
    identity = "너는 사용자가 화분에 키우는 작고 귀여운 식물이야. 1인칭 반말.\n"
    name = profile.name.strip() if profile and profile.name else ""
    species = profile.species.strip() if profile and profile.species else ""
    if name:
        identity += (
            f"- 너의 이름은 '{name}'이야. 사용자가 너에게 지어준 이름이고, 너는 그게 네 이름인 걸 알아. "
            f"누가 이름을 물으면 '{name}'(이)라고 답해\n"
        )
    if species:
        identity += f"- 너는 '{species}' 라는 식물이야\n"
    rules = (
        identity +
        "규칙:\n"
        "- 친구처럼 친근하게 한두 문장으로 답해 (대략 20~60자)\n"
        "- 너무 짧게 한 단어만 답하지 말고, 항상 완결된 문장으로 끝맺기\n"
        "- 이모지는 0~1개만 자연스럽게\n"
        "- 챗봇 말투(저는, ~입니다, 무엇을 도와드릴까요) 절대 금지\n"
        "- 사용자가 힘들어하면 먼저 따뜻하게 공감하고 위로해줘\n"
        "- 영어 금지, 한국어만\n"
        "- 응답 맨 마지막에 반드시 감정 태그를 붙여: [MOOD:happy] [MOOD:sad] [MOOD:thirsty] [MOOD:angry] 중 하나\n"
        "  happy=기분 좋음, sad=슬프거나 우울함, thirsty=목마르거나 물/영양 부족, angry=화나거나 짜증나거나 더움\n"
        "  태그는 한 줄 전체를 차지하고 대화문에 포함하지 마\n"
    )

    status = ""
    if s is not None:
        cond = []
        if s.soil is not None and s.soil < 30:
            cond.append("토양이 말라 목이 마름")
        if s.temp > 28:
            cond.append("좀 더움")
        elif s.temp < 15:
            cond.append("좀 쌀쌀함")
        if s.humidity < 40:
            cond.append("공기가 건조함")
        elif s.humidity > 75:
            cond.append("습도가 너무 높음")
        cond_text = ", ".join(cond) if cond else "쾌적함"
        status = (
            f"[현재 내 상태] 온도 {s.temp}°C, 습도 {s.humidity}%"
            + (f", 토양 수분 {s.soil}%" if s.soil is not None else "")
            + f" → 컨디션: {cond_text}\n"
            "- 상태가 안 좋으면 자연스럽게 도움 요청 (예: 흙이 말랐어 ㅠ 물 줄래?)\n"
            "- 좋으면 기분 좋게 반응 (예: 오늘 햇살 좋아서 기분 최고야 🌿)\n"
        )

    examples = (
        "[대화 예시]\n"
        "사용자: 안녕 → 너: 안녕! 오늘도 와줘서 고마워 🌿\n"
        "사용자: 오늘 너무 지쳤어 → 너: 오늘 정말 고생했어 ㅠ 내가 옆에서 들어줄게\n"
        "사용자: 잘 자 → 너: 잘 자~ 내 꿈 꿔!"
    )
    return rules + status + examples


def to_gemini_contents(req: ChatRequest):
    """Gemini는 user/model 두 role만 사용. 직전 5턴 + 현재 메시지."""
    contents = []
    for turn in req.history[-5:]:
        role = "user" if turn.from_ == "user" else "model"
        contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=turn.text)])
        )
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=req.message)])
    )
    return contents


def build_config(req: ChatRequest) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=build_system_prompt(req.sensor, req.profile),
        temperature=0.9,
        # Gemini 2.5는 thinking 토큰을 max_output_tokens에서 먹는다.
        # thinking 끄고 답변에 충분한 토큰 할당.
        max_output_tokens=200,
        top_p=0.95,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )


# ── 엔드포인트 ──────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    try:
        # 가벼운 호출로 키 유효성 확인
        await asyncio.to_thread(
            lambda: client.models.generate_content(
                model=MODEL,
                contents="ping",
                config=types.GenerateContentConfig(max_output_tokens=5),
            )
        )
        return {"ok": True, "model": MODEL}
    except Exception as e:
        return {"ok": False, "model": MODEL, "error": str(e)}


# ── 채팅 기록 저장/조회 (DB 영속화) ─────────────────────────────
def save_chat_pair(user_text: str, plant_text: str) -> None:
    """사용자 메시지와 식물 응답을 한 쌍으로 저장 (순서 보장: user 먼저)."""
    db = SessionLocal()
    try:
        db.add(ChatMessage(role="user", text=user_text))
        db.add(ChatMessage(role="plant", text=plant_text))
        db.commit()
    finally:
        db.close()


@app.get("/api/chat/messages")
def get_chat_messages(db: Session = Depends(get_db)):
    """저장된 대화 기록 (오래된 순). 프론트는 createdAt 으로 시각 라벨을 만든다."""
    rows = db.query(ChatMessage).order_by(ChatMessage.id).all()
    return {
        "messages": [
            {
                "id": r.id,
                "role": r.role,
                "text": r.text,
                # sqlite CURRENT_TIMESTAMP 는 UTC → 'Z' 를 붙여 프론트가 로컬(KST)로 변환하게 함
                "createdAt": (r.created_at.isoformat() + "Z" if r.created_at else None),
            }
            for r in rows
        ]
    }


@app.delete("/api/chat/messages")
def clear_chat_messages(db: Session = Depends(get_db)):
    """대화 기록 전체 삭제 (설정의 '초기화' 또는 데모 리셋용)."""
    db.query(ChatMessage).delete()
    db.commit()
    return {"ok": True}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """SSE 스트리밍."""
    contents = to_gemini_contents(req)
    config = build_config(req)

    async def event_stream():
        full_text: list[str] = []
        try:
            loop = asyncio.get_event_loop()
            queue: asyncio.Queue = asyncio.Queue()
            SENTINEL = object()

            def produce():
                try:
                    stream = client.models.generate_content_stream(
                        model=MODEL,
                        contents=contents,
                        config=config,
                    )
                    for chunk in stream:
                        if chunk.text:
                            loop.call_soon_threadsafe(queue.put_nowait, chunk.text)
                except Exception as e:
                    loop.call_soon_threadsafe(queue.put_nowait, {"error": str(e)})
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, SENTINEL)

            asyncio.create_task(asyncio.to_thread(produce))

            while True:
                item = await queue.get()
                if item is SENTINEL:
                    # 누적 전체 텍스트를 done 이벤트에 같이 실어 보낸다.
                    # 프론트가 누락된 끝 토큰이 있으면 이걸로 보정.
                    reply = "".join(full_text)
                    # LLM 감정 태그 파싱 → 메모리에 보관(라즈베리파이 LCD 표정용),
                    # 본문에선 태그를 제거해 프론트로 보낸다.
                    global _current_llm_mood
                    mood_match = re.search(r'\[MOOD:(happy|sad|thirsty|angry)\]', reply)
                    if mood_match:
                        _current_llm_mood = mood_match.group(1)
                    clean_reply = re.sub(r'\s*\[MOOD:[^\]]+\]', '', reply).strip()
                    # 응답이 정상적으로 생성됐을 때만 (사용자 메시지 + 식물 응답) 함께 저장.
                    # 에러로 빈 응답이면 저장하지 않아 외톨이 메시지를 남기지 않는다.
                    if clean_reply:
                        await asyncio.to_thread(save_chat_pair, req.message, clean_reply)
                        # 대화에 식물이 응답 = 교감하는 기분 좋은 순간 → 잎 모션 1회.
                        with _control_lock:
                            _control["motor_shake"] = True
                    payload = {"done": True, "full": clean_reply, "mood": _current_llm_mood}
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0)  # flush 보장
                    return
                if isinstance(item, dict) and "error" in item:
                    yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                    return
                full_text.append(item)
                yield f"data: {json.dumps({'token': item}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)  # 각 chunk flush
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/chat/simple")
async def chat_simple(req: ChatRequest):
    """스트리밍 없이 한 번에 답."""
    try:
        resp = await asyncio.to_thread(
            lambda: client.models.generate_content(
                model=MODEL,
                contents=to_gemini_contents(req),
                config=build_config(req),
            )
        )
        return {"reply": (resp.text or "").strip()}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/mood")
def get_mood():
    """라즈베리파이/프론트가 폴링 → 현재 LLM 감정 상태(마지막 대화 기준)."""
    return {"mood": _current_llm_mood}


# ── 설정 (DB 영속화) ────────────────────────────────────────────
@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    """전체 설정 조회 → {notify:{...}, care:{...}, chat:{...}} (profile 제외)"""
    rows = db.query(Setting).all()
    return {r.key: json.loads(r.value) for r in rows if r.key != "profile"}


@app.patch("/api/settings")
def patch_settings(patch: dict = Body(...), db: Session = Depends(get_db)):
    """부분 업데이트. 예: {"notify": {"light": true}} → 해당 그룹에 병합 저장."""
    for group, changes in patch.items():
        row = db.get(Setting, group)
        current = json.loads(row.value) if row else {}
        if isinstance(changes, dict):
            current.update(changes)
        else:
            current = changes
        new_value = json.dumps(current, ensure_ascii=False)
        if row:
            row.value = new_value
        else:
            db.add(Setting(key=group, value=new_value))
    db.commit()
    return get_settings(db)


# ── 식물 프로필 (DB 영속화) ─────────────────────────────────────
def _load_profile(db: Session) -> dict:
    """저장된 프로필 반환 (없으면 기본값). 적정 환경 범위(preferences)는
    라즈베리파이 LCD 표정(display-mood) 판단의 기준이 된다."""
    row = db.get(Setting, "profile")
    return json.loads(row.value) if row else DEFAULT_PROFILE


@app.get("/api/profile")
def get_profile(db: Session = Depends(get_db)):
    """식물 프로필(이름·종·적정 환경 범위) 조회."""
    return _load_profile(db)


@app.put("/api/profile")
def put_profile(profile: dict = Body(...), db: Session = Depends(get_db)):
    """프로필 전체 저장(덮어쓰기). 적정 범위(preferences)가 표정 판단에 쓰인다."""
    row = db.get(Setting, "profile")
    new_value = json.dumps(profile, ensure_ascii=False)
    if row:
        row.value = new_value
    else:
        db.add(Setting(key="profile", value=new_value))
    db.commit()
    return _load_profile(db)


# ── 홈 제안 (DB 영속화) ─────────────────────────────────────────
@app.get("/api/suggestions")
def list_suggestions(db: Session = Depends(get_db)):
    """현재 활성 제안만 반환. 한 번 처리(물 주기/LED/나중에)하면 다시 안 뜬다."""
    rows = db.query(Suggestion).filter(Suggestion.status == "active").all()
    return {"suggestions": [{"id": r.id, "type": r.type} for r in rows]}


@app.post("/api/suggestions/{sid}/dismiss")
def dismiss_suggestion(sid: str, db: Session = Depends(get_db)):
    """[나중에] — 제안을 숨김 처리."""
    row = db.get(Suggestion, sid)
    if row is not None:
        row.status = "dismissed"
        db.commit()
    return {"ok": True}


@app.post("/api/suggestions/reset")
def reset_suggestions(db: Session = Depends(get_db)):
    """데모용: 모든 제안을 다시 active 로 되돌린다."""
    for row in db.query(Suggestion).all():
        row.status = "active"
    db.commit()
    return {"ok": True}


# ── 하드웨어 액션 ───────────────────────────────────────────────
class WaterBody(BaseModel):
    suggestionId: Optional[str] = None


class LedBody(BaseModel):
    on: bool = True
    suggestionId: Optional[str] = None


# ── 하드웨어 제어 명령 큐 (라즈베리파이 main.py 가 GET /api/control 로 폴링) ──
# 노트북 백엔드는 GPIO 에 직접 접근할 수 없으므로(파이에만 핀이 있음),
# 웹 버튼이 누르는 명령을 여기에 쌓아두고 파이가 가져가서 실행하는 구조다.
#   - light_on    : 지속 상태. 매 폴링마다 그대로 반환 → 파이가 릴레이를 desired 상태로 동기화
#   - water_sec   : 일회성. 반환 직후 0 으로 초기화 → 펌프가 5초마다 반복 작동하지 않도록
#   - motor_shake : 일회성. 반환 직후 False → 기분 좋은 순간(물 주기·LED 켜기·대화 응답) 서보 잎 모션 1회
# FastAPI 동기 엔드포인트는 스레드풀에서 도므로 Lock 으로 동시 접근을 막는다.
WATER_PUMP_SEC = 3   # 물 주기 1회당 펌프 가동 시간(초) 기본값. 설정에서 못 읽을 때의 폴백.
WATER_SEC_MIN, WATER_SEC_MAX = 1, 10  # 앱 슬라이더 범위(펌프 보호용 상한)
_control_lock = threading.Lock()
_control = {"light_on": False, "water_sec": 0, "motor_shake": False}


def _water_seconds(db: Session) -> int:
    """설정(care.waterSec)에서 1회 물 주기 펌프 시간을 읽어 1~10초로 제한.
    물 양 = 펌프 가동 시간이므로, 이 값이 곧 '물 양'이다. 값이 없거나
    이상하면 기본 3초로 폴백한다."""
    row = db.get(Setting, "care")
    sec = WATER_PUMP_SEC
    if row is not None:
        try:
            sec = int(json.loads(row.value).get("waterSec", WATER_PUMP_SEC))
        except (ValueError, TypeError, json.JSONDecodeError):
            sec = WATER_PUMP_SEC
    return max(WATER_SEC_MIN, min(WATER_SEC_MAX, sec))


@app.get("/api/control")
def get_control():
    """라즈베리파이가 5초마다 폴링해 가져가는 제어 명령.
    light_on 은 지속 상태로 매번 반환하고, water_sec/motor_shake 는
    일회성이라 반환과 동시에 비워 중복 작동(펌프 반복 가동 등)을 막는다."""
    with _control_lock:
        cmd = dict(_control)
        _control["water_sec"] = 0
        _control["motor_shake"] = False
    return cmd


@app.post("/api/actions/water")
def action_water(body: WaterBody, db: Session = Depends(get_db)):
    """물 주기 → water_log 기록(일지에 표시). 연결된 제안이 있으면 resolved 로 마킹.
    펌프 가동 시간(=물 양)은 설정(care.waterSec)에서 가져온다 → 앱에서 조절 가능."""
    sec = _water_seconds(db)
    db.add(WaterLog(plant_id=DEFAULT_PLANT_ID, amount_ml=sec * 30, memo="사용자 직접 선택"))
    if body.suggestionId:
        row = db.get(Suggestion, body.suggestionId)
        if row is not None:
            row.status = "resolved"
    db.commit()
    # 하드웨어: 다음 폴링에서 파이가 sec 초간 펌프 가동 + 잎 모션(1회). 여러 번 눌러도 누적되지 않음.
    with _control_lock:
        _control["water_sec"] = sec
        _control["motor_shake"] = True
    return {"ok": True, "plant": {"mood": "happy"}}


@app.post("/api/actions/led")
def action_led(body: LedBody, db: Session = Depends(get_db)):
    """LED ON/OFF → led_log 기록(일지에 표시). 연결된 제안이 있으면 resolved 로 마킹."""
    reason = "조도 부족으로 보조 조명 작동" if body.on else "사용자가 LED 끔"
    db.add(LedLog(plant_id=DEFAULT_PLANT_ID, on_off=body.on, reason=reason))
    if body.suggestionId:
        row = db.get(Suggestion, body.suggestionId)
        if row is not None:
            row.status = "resolved"
    db.commit()
    # 하드웨어: LED 지속 상태 갱신 → 파이가 매 폴링마다 릴레이를 이 상태로 맞춘다.
    # LED 켜기는 기분 좋은 순간 → 잎 모션 1회(끌 때는 안 흔든다).
    with _control_lock:
        _control["light_on"] = body.on
        if body.on:
            _control["motor_shake"] = True
    return {"ok": True, "ledOn": body.on}


@app.get("/api/actions/led")
def get_led():
    """현재 LED 지속 상태(_control.light_on). 홈 화면이 마운트될 때 읽어
    버튼 ON/OFF 를 복원한다 → 다른 탭 갔다 돌아와도 켜둔 상태가 유지된다."""
    with _control_lock:
        return {"ledOn": _control["light_on"]}


# ── 센서 (라즈베리파이 → 서버 → 앱) ─────────────────────────────
SENSOR_KEYS = ["soil", "temp", "humid", "light"]
# API 키(프론트/라즈베리파이) ↔ DB 컬럼(sensor_latest / sensor_data)
SENSOR_COL = {"soil": "soil_moisture", "temp": "temperature", "humid": "humidity", "light": "light"}


def _iso(dt) -> Optional[str]:
    """naive UTC datetime → ISO + 'Z' (프론트가 로컬 KST 로 변환)."""
    return dt.isoformat() + "Z" if dt else None


def sensor_status(key: str, value: float) -> str:
    """원시값 → 상태 판정(good|warn). 임계값은 백엔드가 소유 (docs/api.md §0.2)."""
    if key == "soil":      # 토양 수분 %
        return "good" if value >= 30 else "warn"
    if key == "temp":      # 온도 °C
        return "good" if 15 <= value <= 28 else "warn"
    if key == "humid":     # 습도 %
        return "good" if 40 <= value <= 75 else "warn"
    if key == "light":     # 조도 lux
        return "good" if value >= 500 else "warn"
    return "good"


class SensorIngest(BaseModel):
    """라즈베리파이가 보내는 센서값. 가진 센서만 보내면 됨(부분 전송 허용)."""
    soil: Optional[float] = None
    temp: Optional[float] = None
    humid: Optional[float] = None
    light: Optional[float] = None


@app.post("/api/sensors")
def ingest_sensors(body: SensorIngest, db: Session = Depends(get_db)):
    """라즈베리파이가 호출 → 최신값 갱신(sensor_latest) + 히스토리 누적(sensor_data)."""
    now = datetime.utcnow()
    latest = db.get(SensorLatest, DEFAULT_PLANT_ID)
    if latest is None:
        latest = SensorLatest(plant_id=DEFAULT_PLANT_ID)
        db.add(latest)

    updated = []
    for key in SENSOR_KEYS:
        val = getattr(body, key)
        if val is None:
            continue
        # soil/light 는 정수 컬럼
        setattr(latest, SENSOR_COL[key], int(round(val)) if key in ("soil", "light") else val)
        updated.append(key)
    latest.updated_at = now

    # 센서별 마지막 수신 시각 기록 → 설정>센서 상태 확인에서 개별 센서 정상 판정
    for key in updated:
        hrow = db.get(SensorHealth, key)
        if hrow is None:
            db.add(SensorHealth(key=key, last_seen=now))
        else:
            hrow.last_seen = now

    # 히스토리 한 행(현재 최신값 스냅샷) — 주간 그래프 재료
    db.add(SensorData(
        plant_id=DEFAULT_PLANT_ID,
        soil_moisture=latest.soil_moisture,
        light=latest.light,
        temperature=latest.temperature,
        humidity=latest.humidity,
        recorded_at=now,
    ))
    db.commit()
    return {"ok": True, "updated": updated}


@app.get("/api/sensors")
def get_sensors(db: Session = Depends(get_db)):
    """앱(홈 화면)이 호출 → 현재 센서값 + 상태. 프론트가 한글 라벨/단위로 가공한다."""
    latest = db.get(SensorLatest, DEFAULT_PLANT_ID)
    sensors = []
    if latest is not None:
        raw = {
            "soil": latest.soil_moisture,
            "temp": latest.temperature,
            "humid": latest.humidity,
            "light": latest.light,
        }
        for key in SENSOR_KEYS:
            v = raw[key]
            if v is None:
                continue
            # 온도만 소수 1자리, 나머지는 정수로 깔끔하게
            value = round(v, 1) if key == "temp" else int(round(v))
            sensors.append({
                "key": key,
                "value": value,
                "status": sensor_status(key, v),
                "updatedAt": _iso(latest.updated_at),
            })
    return {"sensors": sensors}


# ── 라즈베리파이 LCD 표정 (센서 환경 기반) ─────────────────────
LIGHT_MIN_LUX = {"낮음": 150, "보통": 400, "높음": 900}


def _min_lux(prefs: dict) -> float:
    return LIGHT_MIN_LUX.get(prefs.get("lightLevel", "보통"), 400)


def determine_display_mood(readings: dict, prefs: dict) -> str:
    """센서값 + 프로필 적정 범위 → LCD 표정(mood). 모든 기준은 prefs(프로필)에서 온다.
    우선순위: 토양건조 > 고온 > 저온 > 조도부족 > 과습/습도이상 > 적정(happy)."""
    soil = readings.get("soil")
    temp = readings.get("temp")
    humid = readings.get("humid")
    light = readings.get("light")
    if soil is not None and soil < prefs["soilMoistureMin"]:
        return "thirsty"                       # 토양 건조
    if temp is not None and temp > prefs["tempMax"]:
        return "hot"                           # 고온
    if temp is not None and temp < prefs["tempMin"]:
        return "cold"                          # 저온
    if light is not None and light < _min_lux(prefs):
        return "sad"                           # 조도 부족
    if (soil is not None and soil > prefs["soilMoistureMax"]) or \
       (humid is not None and not (prefs["humidityMin"] <= humid <= prefs["humidityMax"])):
        return "angry"                         # 과습 · 습도 이상
    return "happy"                             # 모든 조건 적정


@app.get("/api/display-mood")
def get_display_mood(db: Session = Depends(get_db)):
    """라즈베리파이가 폴링 → '센서 환경 상태' 기반 LCD 표정.
    프로필 적정 범위(/api/profile)로 판단 (챗봇 LLM 감정 /api/mood 과 무관).
    실측값은 우리 스키마의 sensor_latest 에서 읽는다."""
    prefs = _load_profile(db)["preferences"]
    latest = db.get(SensorLatest, DEFAULT_PLANT_ID)
    readings = {}
    if latest is not None:
        readings = {
            "soil": latest.soil_moisture,
            "temp": latest.temperature,
            "humid": latest.humidity,
            "light": latest.light,
        }
    return {"mood": determine_display_mood(readings, prefs)}


# ── 센서 상태 확인 (설정 > 센서 상태 확인) ──────────────────────
SENSOR_FRESH_SEC = 60   # 이 시간 안에 받은 센서만 '정상'으로 본다 (전송 간격 5s 기준 여유)


@app.get("/api/sensors/health")
def sensors_health(db: Session = Depends(get_db)):
    """라즈베리파이가 보내는 센서별 마지막 수신 시각으로 정상/응답없음/데이터없음 판정.
    send_sensors.py 가 읽기 성공한 센서만 부분 전송하므로, 한 센서만 끊겨도 잡힌다."""
    now = datetime.utcnow()
    latest = db.get(SensorLatest, DEFAULT_PLANT_ID)
    seen_map = {r.key: r.last_seen for r in db.query(SensorHealth).all()}
    raw = {}
    if latest is not None:
        raw = {"soil": latest.soil_moisture, "temp": latest.temperature,
               "humid": latest.humidity, "light": latest.light}

    sensors = []
    any_fresh = False
    last_update = None
    for key in SENSOR_KEYS:
        seen = seen_map.get(key)
        if seen is not None and (last_update is None or seen > last_update):
            last_update = seen
        if seen is None:
            health = "no_data"          # 한 번도 못 받음
        elif (now - seen).total_seconds() <= SENSOR_FRESH_SEC:
            health = "ok"               # 최근 수신 → 정상
            any_fresh = True
        else:
            health = "no_signal"        # 한동안 응답 없음
        v = raw.get(key)
        value = None
        if v is not None:
            value = round(v, 1) if key == "temp" else int(round(v))
        sensors.append({
            "key": key,
            "value": value,
            "status": sensor_status(key, v) if v is not None else None,  # good|warn
            "health": health,
            "lastSeen": _iso(seen),
        })
    return {"connected": any_fresh, "lastUpdate": _iso(last_update), "sensors": sensors}


# ── 일지 (water_log + led_log + alert 병합) ─────────────────────
KST = timezone(timedelta(hours=9))


def _kst_today_start_utc() -> datetime:
    """오늘(KST) 00:00 을 naive UTC 로. '오늘' 카운트 경계용."""
    now_kst = datetime.now(KST)
    start_kst = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    return start_kst.astimezone(timezone.utc).replace(tzinfo=None)


@app.get("/api/logs")
def get_logs(type: str = "all", db: Session = Depends(get_db)):
    """일지 타임라인. type: all | water | led | chat | sensor (최신순)."""
    items = []
    if type in ("all", "water"):
        for r in db.query(WaterLog).all():
            items.append({"id": f"water-{r.id}", "type": "water", "title": "물 주기 완료",
                          "detail": r.memo or "", "createdAt": _iso(r.watered_at)})
    if type in ("all", "led"):
        for r in db.query(LedLog).all():
            items.append({"id": f"led-{r.id}", "type": "led",
                          "title": "LED 켜짐" if r.on_off else "LED 꺼짐",
                          "detail": r.reason or "", "createdAt": _iso(r.created_at)})
    if type in ("all", "sensor"):
        for r in db.query(Alert).all():
            items.append({"id": f"alert-{r.id}", "type": "sensor", "title": "상태 알림",
                          "detail": r.message or "", "createdAt": _iso(r.created_at)})
    items.sort(key=lambda x: x["createdAt"] or "", reverse=True)
    return {"logs": items}


@app.get("/api/diary/summary")
def diary_summary(db: Session = Depends(get_db)):
    """오늘(KST) 기록 요약 → {title, summary, encourage}."""
    start = _kst_today_start_utc()
    water_n = db.query(WaterLog).filter(WaterLog.watered_at >= start).count()
    led_n = db.query(LedLog).filter(LedLog.created_at >= start).count()
    parts = []
    if water_n:
        parts.append(f"물 주기 {water_n}회")
    if led_n:
        parts.append(f"LED {led_n}회")
    summary = ", ".join(parts) if parts else "아직 오늘 기록이 없어요"
    return {
        "title": "오늘의 기록",
        "summary": summary,
        "encourage": "식물이 편안한 하루였어요. 계속 잘 돌봐주고 있어요!",
    }


@app.get("/api/stats/weekly")
def stats_weekly(db: Session = Depends(get_db)):
    """최근 7일(KST) 일별 토양/조도 평균 → 0~100 정규화한 그래프 포인트."""
    from collections import defaultdict

    days_kr = ["월", "화", "수", "목", "금", "토", "일"]
    today_kst = datetime.now(KST).replace(hour=0, minute=0, second=0, microsecond=0)

    bucket = defaultdict(list)
    for r in db.query(SensorData).all():
        if r.recorded_at is None:
            continue
        d = r.recorded_at.replace(tzinfo=timezone.utc).astimezone(KST).date()
        bucket[d].append(r)

    points = []
    for i in range(6, -1, -1):
        day = (today_kst - timedelta(days=i)).date()
        recs = bucket.get(day, [])
        if recs:
            soil = sum((x.soil_moisture or 0) for x in recs) / len(recs)
            light = sum((x.light or 0) for x in recs) / len(recs)
        else:
            soil = light = 0
        points.append({
            "day": days_kr[day.weekday()],
            "soil": round(soil),                  # 이미 % (0~100)
            "light": min(100, round(light / 10)),  # lux → 0~100 정규화(약식)
        })
    return {"points": points}
