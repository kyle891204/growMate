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
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from database import Base, engine
load_dotenv()

#db 연동
Base.metadata.create_all(bind=engine)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("MODEL", "gemini-2.5-flash")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY 환경변수가 없음. .env를 확인하세요. "
        "키 발급: https://aistudio.google.com/apikey"
    )

client = genai.Client(api_key=GEMINI_API_KEY)

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
    sensor: Sensor
    history: List[ChatTurn] = []


# ── 식물 페르소나 system prompt ────────────────────────────────
def build_system_prompt(s: Sensor) -> str:
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

    return (
        "너는 사용자가 화분에 키우는 작고 귀여운 식물이야. 1인칭 반말.\n"
        "규칙:\n"
        "- 친구처럼 친근하게 한두 문장으로 답해 (대략 20~60자)\n"
        "- 너무 짧게 한 단어만 답하지 말고, 항상 완결된 문장으로 끝맺기\n"
        "- 이모지는 0~1개만 자연스럽게\n"
        "- 챗봇 말투(저는, ~입니다, 무엇을 도와드릴까요) 절대 금지\n"
        "- 영어 금지, 한국어만\n"
        f"[현재 내 상태] 온도 {s.temp}°C, 습도 {s.humidity}%"
        + (f", 토양 수분 {s.soil}%" if s.soil is not None else "")
        + f" → 컨디션: {cond_text}\n"
        "- 상태가 안 좋으면 자연스럽게 도움 요청 (예: 흙이 말랐어 ㅠ 물 줄래?)\n"
        "- 좋으면 기분 좋게 반응 (예: 오늘 햇살 좋아서 기분 최고야 🌿)\n"
        "[대화 예시]\n"
        "사용자: 안녕 → 너: 안녕! 오늘도 와줘서 고마워 🌿\n"
        "사용자: 물 줘? → 너: 응 응! 흙이 너무 말랐어 ㅠㅠ\n"
        "사용자: 잘 자 → 너: 잘 자~ 내 꿈 꿔!"
    )


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
                    payload = {"done": True, "full": "".join(full_text)}
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
