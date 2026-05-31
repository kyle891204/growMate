// 홈 화면에서 식물이 사용자에게 건네는 제안 (mock)
// type: water(물 주기 제안 - 액션 버튼 있음) | light(조도 부족 - 안내성)
export const suggestions = [
  {
    id: "water",
    type: "water",
    message: "조금 목말라요. 물을 줄까요?",
    primary: "물 주기",
    secondary: "나중에",
  },
  {
    id: "light",
    type: "light",
    message: "조금 어두운 것 같아요. 빛이 더 필요할지도 몰라요.",
    primary: "LED 켜기",
    secondary: "나중에",
  },
];
