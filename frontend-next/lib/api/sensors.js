// 센서 요약 API — docs/api.md §1.2
import { apiFetch, USE_MOCK, mockDelay } from "./client";
import { sensors, sensorReadings } from "@/lib/data/sensors";

// GET /sensors — 홈 2x2 센서 카드
// ⚠️ 실제 백엔드 응답은 value 가 "숫자"(예: 24)이고 status(good|warn)만 옵니다 (docs/api.md §0.2).
//    한글 라벨 / 단위 / note / icon 은 프론트가 key·status 로 매핑합니다. → toView() 가 그 자리.
export function getSensors() {
  if (USE_MOCK) return mockDelay(sensors);
  return apiFetch("/sensors").then((data) => data.sensors.map(toView));
}

// GET /sensors → 원시 측정값만 추출 ({ soilMoisture, temperature, humidity, lightLux }).
// 식물 프로필의 권장 범위로 평가(evaluateSensors)하려면 숫자 원시값이 필요하다.
export function getSensorReadings() {
  if (USE_MOCK) return mockDelay(sensorReadings);
  return apiFetch("/sensors").then((data) => {
    const v = Object.fromEntries(data.sensors.map((s) => [s.key, s.value]));
    return {
      soilMoisture: v.soil,
      temperature: v.temp,
      humidity: v.humid,
      lightLux: v.light,
    };
  });
}

// GET /sensors/health — 설정 > 센서 상태 확인 (라즈베리파이 센서별 정상 여부)
// health: "ok"(정상·최근수신) | "no_signal"(응답없음) | "no_data"(한번도 못받음)
export function getSensorHealth() {
  if (USE_MOCK) {
    const nowIso = new Date().toISOString();
    return mockDelay({
      connected: true,
      lastUpdate: nowIso,
      sensors: [
        { key: "soil", value: 42, status: "good", health: "ok", lastSeen: nowIso },
        { key: "temp", value: 24.5, status: "good", health: "ok", lastSeen: nowIso },
        { key: "humid", value: 55, status: "good", health: "ok", lastSeen: nowIso },
        { key: "light", value: 600, status: "good", health: "ok", lastSeen: nowIso },
      ],
    });
  }
  return apiFetch("/sensors/health");
}

// 백엔드 원시 데이터 → 화면 표시용 변환
function toView(s) {
  const META = {
    soil: { label: "토양 수분", icon: "droplet", unit: "%" },
    temp: { label: "온도", icon: "thermo", unit: "°C" },
    humid: { label: "습도", icon: "humidity", unit: "%" },
    light: { label: "조도", icon: "sun", unit: "lux" },
  };
  const meta = META[s.key] || {};
  return {
    key: s.key,
    label: meta.label,
    value: `${s.value}${meta.unit || ""}`,
    note: s.status === "warn" ? "주의" : "적정", // TODO: key별 세분화(건조 / 다소 낮음 등)
    status: s.status,
    icon: meta.icon,
  };
}
