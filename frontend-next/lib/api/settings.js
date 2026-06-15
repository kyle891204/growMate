// 설정 API — docs/api.md §4
import { apiFetch, USE_MOCK, mockDelay } from "./client";
import { notifySettings, careSettings, chatSettings } from "@/lib/data/settings";

// GET /settings — 전체 설정 조회
export function getSettings() {
  if (USE_MOCK) {
    const toObj = (arr) => Object.fromEntries(arr.map((s) => [s.key, s.value]));
    return mockDelay({
      notify: toObj(notifySettings),
      care: { ...toObj(careSettings), waterSec: 3 },
      chat: toObj(chatSettings),
    });
  }
  return apiFetch("/settings");
}

// PATCH /settings — 부분 업데이트. 예: updateSettings({ notify: { light: true } })
export function updateSettings(patch) {
  if (USE_MOCK) return mockDelay(patch);
  return apiFetch("/settings", { method: "PATCH", body: patch });
}
