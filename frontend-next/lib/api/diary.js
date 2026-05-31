// 일지 API — docs/api.md §3
import { apiFetch, USE_MOCK, mockDelay } from "./client";
import { logs, todaySummary, weekly } from "@/lib/data/logs";

// GET /logs?type= — 타임라인 (type: all | water | led | chat | sensor)
export function getLogs(type = "all") {
  if (USE_MOCK) {
    const filtered = type === "all" ? logs : logs.filter((l) => l.type === type);
    return mockDelay(filtered);
  }
  const q = type && type !== "all" ? `?type=${type}` : "";
  return apiFetch(`/logs${q}`).then((data) => data.logs);
  // 표시용 "14:21" 변환은 화면에서 createdAt(ISO)로 처리
}

// GET /diary/summary — 오늘의 기록 요약
export function getDiarySummary() {
  if (USE_MOCK) return mockDelay(todaySummary);
  return apiFetch("/diary/summary");
  // ⚠️ 실제 응답이 { counts, stable } 형태면 여기서 "오늘 물 주기 N회..." 문장으로 조합 (docs/api.md §3.2)
}

// GET /stats/weekly — 주간 변화 그래프
export function getWeeklyStats() {
  if (USE_MOCK) return mockDelay(weekly);
  return apiFetch("/stats/weekly").then((data) => data.points);
  // ⚠️ 원시값(soil %, light lux)이면 차트용 0~100 정규화 필요 (docs/api.md §3.3)
}
