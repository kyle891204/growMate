// 공감채팅 API — docs/api.md §2.1, §2.2
import { apiFetch, USE_MOCK, mockDelay } from "./client";
import { initialMessages, getPlantReply } from "@/lib/data/chat";

// GET /chat/messages — 대화 기록
export function getMessages() {
  if (USE_MOCK) return mockDelay(initialMessages);
  return apiFetch("/chat/messages").then((data) => data.messages);
}

// POST /chat — 메시지 전송 + 식물(LLM) 응답
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
