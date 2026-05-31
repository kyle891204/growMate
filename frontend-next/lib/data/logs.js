// 일지 타임라인 (mock). type: water | led | chat | sensor
export const logs = [
  {
    id: 1,
    time: "14:21",
    type: "water",
    title: "물 주기 완료",
    detail: "사용자 직접 선택",
  },
  {
    id: 2,
    time: "15:00",
    type: "led",
    title: "LED 켜짐",
    detail: "조도 부족으로 보조 조명 작동",
  },
  {
    id: 3,
    time: "17:10",
    type: "chat",
    title: "기분 대화",
    detail: "사용자 감정: 지침 / 식물 반응: 위로 메시지",
  },
  {
    id: 4,
    time: "18:30",
    type: "sensor",
    title: "상태 안정",
    detail: "토양 수분 정상, 조도 정상",
  },
];

// 필터 칩 정의 (key는 logs.type과 매칭, all은 전체)
export const logFilters = [
  { key: "all", label: "전체" },
  { key: "water", label: "급수" },
  { key: "led", label: "LED" },
  { key: "chat", label: "대화" },
  { key: "sensor", label: "센서" },
];

// 오늘의 기록 요약
export const todaySummary = {
  title: "오늘의 기록",
  summary: "오늘 물 주기 1회, LED 2회, 상태 안정",
  encourage: "식물이 편안한 하루였어요. 계속 잘 돌봐주고 있어요!",
};

// 주간 변화 그래프 데이터 (최근 7일). 값은 0~100 정규화 스케일.
// soil: 토양 수분, light: 조도
export const weekly = [
  { day: "월", soil: 62, light: 48 },
  { day: "화", soil: 55, light: 60 },
  { day: "수", soil: 40, light: 35 },
  { day: "목", soil: 70, light: 72 },
  { day: "금", soil: 58, light: 50 },
  { day: "토", soil: 33, light: 42 },
  { day: "일", soil: 24, light: 38 },
];
