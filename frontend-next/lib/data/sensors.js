// 센서 원시값 (mock) — 추후 API로 교체
export const sensorReadings = {
  soilMoisture: 45,  // %
  temperature: 23.4, // °C
  humidity: 58,      // %
  lightLux: 520,     // lux
};

// 조도 선호별 최소 lux 기준
const LIGHT_MIN_LUX = { "낮음": 150, "보통": 400, "높음": 900 };

function evalRange(val, min, max, belowNote, aboveNote) {
  if (val < min) return { status: "warn", note: belowNote };
  if (val > max) return { status: "warn", note: aboveNote };
  return { status: "good", note: "적정" };
}

// 프로필 환경 선호 기준으로 센서 상태 평가
export function evaluateSensors(readings, prefs) {
  const { soilMoisture, temperature, humidity, lightLux } = readings;
  const {
    soilMoistureMin, soilMoistureMax,
    tempMin, tempMax,
    humidityMin, humidityMax,
    lightLevel,
  } = prefs;

  const minLux = LIGHT_MIN_LUX[lightLevel] ?? 400;
  const lightOk = lightLux >= minLux;

  const lightLabel = { "낮음": "150", "보통": "400", "높음": "900" }[lightLevel] ?? "400";

  return [
    {
      key: "soil",
      label: "토양 수분",
      value: `${soilMoisture}%`,
      icon: "droplet",
      target: `${soilMoistureMin}–${soilMoistureMax}%`,
      ...evalRange(soilMoisture, soilMoistureMin, soilMoistureMax, "건조", "과습"),
    },
    {
      key: "temp",
      label: "온도",
      value: `${temperature}°C`,
      icon: "thermo",
      target: `${tempMin}–${tempMax}°C`,
      ...evalRange(temperature, tempMin, tempMax, "저온", "고온"),
    },
    {
      key: "humid",
      label: "습도",
      value: `${humidity}%`,
      icon: "humidity",
      target: `${humidityMin}–${humidityMax}%`,
      ...evalRange(humidity, humidityMin, humidityMax, "건조", "과습"),
    },
    {
      key: "light",
      label: "조도",
      value: `${lightLux} lux`,
      icon: "sun",
      target: `${lightLabel} lux 이상`,
      status: lightOk ? "good" : "warn",
      note: lightOk ? "적정" : "부족",
    },
  ];
}
