// GrowMate API 레이어 진입점. 계약 문서: docs/api.md
// 사용 예) import { getSensors, waterPlant } from "@/lib/api";
export * from "./plant";
export * from "./sensors";
export * from "./suggestions";
export * from "./actions";
export * from "./chat";
export * from "./diary";
export * from "./settings";
export { API_BASE, USE_MOCK, ApiError } from "./client";
