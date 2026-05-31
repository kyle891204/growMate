// 센서 요약 (mock)
// status: good(적정) | warn(주의/건조/낮음)
export const sensors = [
  { key: "soil", label: "토양 수분", value: "24%", note: "건조", status: "warn", icon: "droplet" },
  { key: "temp", label: "온도", value: "24.6°C", note: "적정", status: "good", icon: "thermo" },
  { key: "humid", label: "습도", value: "58%", note: "적정", status: "good", icon: "humidity" },
  { key: "light", label: "조도", value: "520 lux", note: "다소 낮음", status: "warn", icon: "sun" },
];
