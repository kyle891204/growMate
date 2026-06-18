// 공감채팅 API — docs/api.md §2.1, §2.2
import { API_BASE, apiFetch, USE_MOCK, mockDelay } from "./client";
import { initialMessages, getPlantReply } from "@/lib/data/chat";

// GET /chat/messages — 대화 기록
export function getMessages() {
  if (USE_MOCK) return mockDelay(initialMessages);
  return apiFetch("/chat/messages").then((data) => data.messages);
}

// DELETE /chat/messages — 대화 기록 전체 삭제 (대화 초기화)
export function clearMessages() {
  if (USE_MOCK) return mockDelay({ ok: true });
  return apiFetch("/chat/messages", { method: "DELETE" });
}

// POST /chat — 메시지 전송 + 식물(LLM) 응답 (한 번에)
// ⚠️ mock 은 키워드 매칭(getPlantReply)으로 답합니다. 실제로는 백엔드 LLM 이 reply 를 생성합니다.
export function sendMessage(text) {
  if (USE_MOCK) {
    const now = new Date().toISOString();
    return mockDelay(
      {
        userMessage: { id: Date.now(), role: "user", text, createdAt: now },
        reply: { id: Date.now() + 1, role: "plant", text: getPlantReply(text), createdAt: now },
      },
      400
    );
  }
  return apiFetch("/chat", { method: "POST", body: { text } });
}

// POST /chat (SSE) — 토큰 스트리밍. 식물이 한 글자씩 타이핑하듯 답한다.
//   history: [{ role: 'user'|'plant', text }] (최근 순서대로), 백엔드는 마지막 5턴만 사용.
//   콜백: onToken(누적 X, 새 조각), onDone(전체 텍스트), onError(Error)
// mock 모드(NEXT_PUBLIC_API_BASE_URL 미설정)에서는 키워드 응답을 흉내내어 스트리밍한다.
export async function streamMessage(
  { message, history = [], sensor = null, profile = null },
  { onToken, onDone, onError, signal } = {}
) {
  if (USE_MOCK) {
    const reply = getPlantReply(message);
    let acc = "";
    for (const ch of reply) {
      if (signal?.aborted) return;
      acc += ch;
      onToken?.(ch);
      await new Promise((r) => setTimeout(r, 18));
    }
    onDone?.(acc);
    return;
  }

  try {
    const body = { message, history };
    if (sensor) body.sensor = sensor;
    if (profile) body.profile = profile;
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
    if (!res.ok || !res.body) {
      throw new Error(`채팅 요청 실패 (${res.status})`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let full = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // SSE 프레임은 빈 줄(\n\n)로 구분된다.
      let sep;
      while ((sep = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, sep).trim();
        buffer = buffer.slice(sep + 2);
        if (!frame.startsWith("data:")) continue;
        const json = frame.slice(5).trim();
        if (!json) continue;
        let data;
        try {
          data = JSON.parse(json);
        } catch {
          continue;
        }
        if (data.error) {
          throw new Error(data.error);
        }
        if (data.token) {
          full += data.token;
          onToken?.(data.token);
        }
        if (data.done) {
          full = data.full ?? full;
        }
      }
    }
    onDone?.(full);
  } catch (err) {
    if (err?.name === "AbortError") return;
    onError?.(err);
  }
}
