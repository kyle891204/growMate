// 하드웨어 제어 API — docs/api.md §1.4, §1.5
// GrowMate 의 핵심: 대화/제안이 실제 펌프·LED 제어로 연결되는 지점.
import { apiFetch, USE_MOCK, mockDelay } from "./client";

// POST /actions/water — 펌프 작동(물 주기)
export function waterPlant(suggestionId) {
  if (USE_MOCK) {
    return mockDelay({
      ok: true,
      log: {
        id: Date.now(),
        type: "water",
        title: "물 주기 완료",
        detail: "사용자 직접 선택",
        createdAt: new Date().toISOString(),
      },
      plant: { mood: "happy" },
    });
  }
  return apiFetch("/actions/water", { method: "POST", body: { suggestionId } });
}

// POST /actions/led — LED ON/OFF. suggestionId 를 주면 해당 제안을 처리완료로 마킹.
export function setLed(on, suggestionId) {
  if (USE_MOCK) {
    return mockDelay({
      ok: true,
      ledOn: on,
      log: {
        id: Date.now(),
        type: "led",
        title: on ? "LED 켜짐" : "LED 꺼짐",
        detail: "사용자 직접 선택",
        createdAt: new Date().toISOString(),
      },
    });
  }
  return apiFetch("/actions/led", { method: "POST", body: { on, suggestionId } });
}

// GET /actions/led — 현재 LED 상태. 홈 진입 시 버튼 ON/OFF 복원에 쓴다.
export function getLed() {
  if (USE_MOCK) {
    return mockDelay({ ledOn: false });
  }
  return apiFetch("/actions/led");
}
