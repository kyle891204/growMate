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
from datetime import datetime, timezone
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
    from models import ChatMessage, SensorReading, Setting, Suggestion, seed_defaults
except ModuleNotFoundError:
    from backend.database import Base, engine, get_db, SessionLocal
    from backend import models  # noqa: F401
    from backend.models import ChatMessage, SensorReading, Setting, Suggestion, seed_defaults

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

# LLM이 마지막으로 출력한 감정 태그를 메모리에 보관
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


class ChatRequest(BaseModel):
    message: str
    # 공감채팅은 센서 없이도 동작한다(감정 공감 중심). 있으면 페르소나에 컨디션 반영.
    sensor: Optional[Sensor] = None
    history: List[ChatTurn] = []


# ── 식물 페르소나 system prompt ────────────────────────────────
def build_system_prompt(s: Optional[Sensor]) -> str:
    rules = (
        "너는 사용자가 화분에 키우는 작고 귀여운 식물이야. 1인칭 반말.\n"
        "규칙:\n"
        "- 친구처럼 친근하게 한두 문장으로 답해 (대략 20~60자)\n"
        "- 너무 짧게 한 단어만 답하지 말고, 항상 완결된 문장으로 끝맺기\n"
        "- 이모지는 0~1개만 자연스럽게\n"
        "- 챗봇 말투(저는, ~입니다, 무엇을 도와드릴까요) 절대 금지\n"
        "- 사용자가 힘들어하면 먼저 따뜻하게 공감하고 위로해줘\n"
        "- 영어 금지, 한국어만\n"
        "- 응답 맨 마지막에 반드시 감정 태그를 붙여: [MOOD:happy] [MOOD:sad] [MOOD:stressed] [MOOD:sleepy] 중 하나\n"
        "  happy=기분 좋음, sad=슬프거나 물/영양 부족, stressed=힘들거나 더움, sleepy=졸리거나 빛 부족\n"
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
        system_instruction=build_system_prompt(req.sensor),
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

                    # LLM 감정 태그 파싱 및 저장
                    global _current_llm_mood
                    mood_match = re.search(r'\[MOOD:(happy|sad|stressed|sleepy)\]', reply)
                    if mood_match:
                        _current_llm_mood = mood_match.group(1)
                    # 태그를 프론트로 보내기 전에 텍스트에서 제거
                    clean_reply = re.sub(r'\s*\[MOOD:[^\]]+\]', '', reply).strip()

                    # 응답이 정상적으로 생성됐을 때만 (사용자 메시지 + 식물 응답) 함께 저장.
                    # 에러로 빈 응답이면 저장하지 않아 외톨이 메시지를 남기지 않는다.
                    if clean_reply:
                        await asyncio.to_thread(save_chat_pair, req.message, clean_reply)
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
    """라즈베리파이가 폴링해서 현재 LLM 감정 상태를 가져간다."""
    return {"mood": _current_llm_mood}


# ── 설정 (DB 영속화) ────────────────────────────────────────────
@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    """전체 설정 조회 → {notify:{...}, care:{...}, chat:{...}}"""
    rows = db.query(Setting).all()
    return {r.key: json.loads(r.value) for r in rows}


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


@app.post("/api/actions/water")
def action_water(body: WaterBody, db: Session = Depends(get_db)):
    """물 주기. 연결된 제안이 있으면 resolved 로 마킹."""
    if body.suggestionId:
        row = db.get(Suggestion, body.suggestionId)
        if row is not None:
            row.status = "resolved"
            db.commit()
    # TODO(하드웨어): 여기서 워터펌프 GPIO 작동 (릴레이/MOSFET)
    return {"ok": True, "plant": {"mood": "happy"}}


@app.post("/api/actions/led")
def action_led(body: LedBody, db: Session = Depends(get_db)):
    """LED ON/OFF. 연결된 제안이 있으면 resolved 로 마킹."""
    if body.suggestionId:
        row = db.get(Suggestion, body.suggestionId)
        if row is not None:
            row.status = "resolved"
            db.commit()
    # TODO(하드웨어): 여기서 식물 생장 LED ON/OFF 제어
    return {"ok": True, "ledOn": body.on}


# ── 센서 (라즈베리파이 → 서버 → 앱) ─────────────────────────────
SENSOR_KEYS = ["soil", "temp", "humid", "light"]


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
    """라즈베리파이가 호출 → 최신 센서값 저장(upsert)."""
    now = datetime.now(timezone.utc)
    updated = []
    for key in SENSOR_KEYS:
        val = getattr(body, key)
        if val is None:
            continue
        row = db.get(SensorReading, key)
        if row is not None:
            row.value = val
            row.updated_at = now
        else:
            db.add(SensorReading(key=key, value=val, updated_at=now))
        updated.append(key)
    db.commit()
    return {"ok": True, "updated": updated}


@app.get("/api/sensors")
def get_sensors(db: Session = Depends(get_db)):
    """앱(홈 화면)이 호출 → 현재 센서값 + 상태. 프론트가 한글 라벨/단위로 가공한다."""
    rows = {r.key: r for r in db.query(SensorReading).all()}
    sensors = []
    for key in SENSOR_KEYS:
        r = rows.get(key)
        if r is None:
            continue
        # 온도만 소수 1자리, 나머지는 정수로 깔끔하게
        value = round(r.value, 1) if key == "temp" else int(round(r.value))
        sensors.append({
            "key": key,
            "value": value,
            "status": sensor_status(key, r.value),
            "updatedAt": (r.updated_at.isoformat() + "Z" if r.updated_at else None),
        })
    return {"sensors": sensors}
