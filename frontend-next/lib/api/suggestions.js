// 돌봄 제안 API — docs/api.md §1.3, §1.6
import { apiFetch, USE_MOCK, mockDelay } from "./client";
import { suggestions } from "@/lib/data/suggestions";

// GET /suggestions — 홈 말풍선 제안
// ⚠️ 실제 응답은 { id, type } 만 옵니다. 말풍선 문구/버튼 라벨은 프론트 소유(type별 매핑) → toView().
export function getSuggestions() {
  if (USE_MOCK) return mockDelay(suggestions);
  return apiFetch("/suggestions").then((data) => data.suggestions.map(toView));
}

const COPY = {
  water: { message: "조금 목말라요. 물을 줄까요?", primary: "물 주기", secondary: "나중에" },
  light: { message: "조금 어두운 것 같아요. 빛이 더 필요할지도 몰라요.", primary: "LED 켜기", secondary: "나중에" },
};
function toView(s) {
  return { id: s.id, type: s.type, ...COPY[s.type] };
}

// POST /suggestions/{id}/dismiss — [나중에]
export function dismissSuggestion(id) {
  if (USE_MOCK) return mockDelay({ ok: true });
  return apiFetch(`/suggestions/${id}/dismiss`, { method: "POST" });
}
