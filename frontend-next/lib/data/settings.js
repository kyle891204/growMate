// 설정 화면 초기값 (mock)

// 알림 설정 — 와이어프레임 기준: 조도 부족 알림 OFF
export const notifySettings = [
  { key: "water", label: "물 주기 알림", value: true },
  { key: "light", label: "조도 부족 알림", value: false },
  { key: "chat", label: "공감채팅 알림", value: true },
];

// 돌봄 모드 — 와이어프레임 기준: 제안 메시지 표시 OFF
export const careSettings = [
  { key: "autoProtect", label: "자동 보호 모드", value: true },
  { key: "ledAuto", label: "LED 자동 보조", value: true },
  { key: "showSuggest", label: "제안 메시지 표시", value: false },
];

// 공감채팅 설정 (식물 별명은 프로필 화면과 중복되어 제거)
export const chatSettings = [
  { key: "saveHistory", label: "대화 기록 저장", value: true, type: "toggle" },
  { key: "tone", label: "감정 공감 톤", value: "따뜻하게", type: "value" },
];

// 연결 및 시스템
export const systemMenu = [
  { key: "sensorCheck", label: "센서 상태 확인" },
];

// 식물 프로필 카드
export const profile = {
  name: "그로우메이트",
  meta: "몬스테라 · 연결 정상",
};
