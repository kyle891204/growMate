// 공감채팅 초기 메시지 (mock). role: 'user' | 'plant'
export const initialMessages = [
  {
    id: 1,
    role: "user",
    text: "오늘 과제도 많고 너무 지쳤어.",
    time: "오후 5:08",
  },
  {
    id: 2,
    role: "plant",
    text: "오늘 정말 고생 많았어요. 많이 지쳤겠네요. 잠깐 숨을 고르고, 제가 옆에서 들어드릴게요.",
    time: "오후 5:08",
  },
  {
    id: 3,
    role: "user",
    text: "괜히 마음이 불안해.",
    time: "오후 5:10",
  },
  {
    id: 4,
    role: "plant",
    text: "그럴 수 있어요. 지금처럼 솔직하게 말해주는 것만으로도 잘하고 있어요. 오늘 가장 힘들었던 순간이 언제였나요?",
    time: "오후 5:10",
  },
];

// 추천 프롬프트 칩
export const promptChips = [
  "오늘 너무 힘들었어",
  "위로해줘",
  "기분이 불안해",
  "오늘 잘한 일 알려줘",
];

// 사용자 입력에 대한 식물의 공감 응답 (mock). 키워드가 없으면 기본 응답.
const replyTable = [
  { match: ["힘들", "지쳤", "지침", "피곤"], reply: "오늘 정말 애썼어요. 그 마음, 충분히 그럴 만해요. 잠깐 저랑 같이 숨 한 번 고를까요?" },
  { match: ["불안", "걱정", "초조"], reply: "마음이 불안할 땐 그 감정을 밀어내지 않아도 괜찮아요. 지금 느끼는 그대로 제게 천천히 말해주세요." },
  { match: ["위로"], reply: "당신은 오늘도 충분히 잘 버텨냈어요. 제가 여기 늘 같은 자리에서 응원하고 있을게요." },
  { match: ["잘한", "칭찬", "뿌듯"], reply: "오늘 하루를 끝까지 살아낸 것 자체가 잘한 일이에요. 작은 것 하나라도 스스로를 칭찬해 주세요." },
  { match: ["슬프", "우울", "눈물"], reply: "슬픈 날도 있는 거예요. 울고 싶으면 울어도 돼요. 제가 곁에서 조용히 함께 있어 줄게요." },
];

export function getPlantReply(userText) {
  const found = replyTable.find((r) => r.match.some((m) => userText.includes(m)));
  return found
    ? found.reply
    : "이야기해줘서 고마워요. 당신의 하루를 제가 함께 느끼고 있어요. 조금 더 들려줄 수 있나요?";
}
