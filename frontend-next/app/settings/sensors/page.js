"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DropletIcon, ThermoIcon, HumidityIcon, SunIcon } from "@/components/Icons";
import { getSensorHealth } from "@/lib/api";
import styles from "./sensors.module.css";

const META = {
  soil: { label: "토양 수분", unit: "%", Icon: DropletIcon },
  temp: { label: "온도", unit: "°C", Icon: ThermoIcon },
  humid: { label: "습도", unit: "%", Icon: HumidityIcon },
  light: { label: "조도", unit: "lux", Icon: SunIcon },
};
const ORDER = ["soil", "temp", "humid", "light"];

const HEALTH = {
  ok: { text: "정상", cls: "ok" },
  no_signal: { text: "응답 없음", cls: "warn" },
  no_data: { text: "데이터 없음", cls: "muted" },
};

// ISO(UTC) → "방금 / N초 전 / N분 전 ..."
function relTime(iso) {
  if (!iso) return "—";
  const s = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000));
  if (s < 5) return "방금";
  if (s < 60) return `${s}초 전`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}분 전`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}시간 전`;
  return `${Math.floor(h / 24)}일 전`;
}

const POLL_MS = 5000; // 5초마다 갱신 → 살아있는 상태처럼 보인다

export default function SensorHealthPage() {
  const router = useRouter();
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = () =>
      getSensorHealth()
        .then((d) => {
          if (!alive) return;
          setData(d);
          setError(false);
        })
        .catch((e) => {
          console.error("센서 상태 불러오기 실패:", e);
          if (alive) setError(true);
        });
    load();
    const t = setInterval(load, POLL_MS);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  const sensors = data?.sensors ?? [];
  const connected = data?.connected;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <button className={styles.back} onClick={() => router.back()} aria-label="뒤로">
          ‹
        </button>
        <h1 className={styles.title}>센서 상태 확인</h1>
        <span className={styles.headerPad} />
      </header>

      {/* 연결 상태 배너 */}
      <div className={`${styles.banner} ${connected ? styles.bannerOk : styles.bannerWarn}`}>
        <span className={styles.dot} />
        <div>
          <div className={styles.bannerTitle}>
            {data == null
              ? "확인 중…"
              : connected
              ? "라즈베리파이 연결됨"
              : "센서 데이터가 안 들어오고 있어요"}
          </div>
          <div className={styles.bannerSub}>
            {error
              ? "백엔드에 연결할 수 없어요 (서버 실행 확인)"
              : data?.lastUpdate
              ? `마지막 수신 ${relTime(data.lastUpdate)}`
              : "아직 한 번도 수신 못 함"}
          </div>
        </div>
      </div>

      {/* 센서별 상태 */}
      <div className={styles.list}>
        {ORDER.map((key) => {
          const meta = META[key];
          const Icon = meta.Icon;
          const s = sensors.find((x) => x.key === key);
          const health = HEALTH[s?.health] || HEALTH.no_data;
          // 한 번도 수신 못 한 센서는 시드 기본값 대신 "—" 표시
          const hasValue = s && s.value != null && s.health !== "no_data";
          const seenLabel =
            s && (s.health === "ok" || s.health === "no_signal")
              ? `마지막 수신 ${relTime(s.lastSeen)}`
              : "수신 기록 없음";
          return (
            <div key={key} className={styles.row}>
              <span className={styles.icon}>
                <Icon size={20} color="currentColor" />
              </span>
              <div className={styles.rowBody}>
                <div className={styles.rowLabel}>{meta.label}</div>
                <div className={styles.rowSub}>{seenLabel}</div>
              </div>
              <div className={styles.rowRight}>
                <div className={styles.value}>{hasValue ? `${s.value}${meta.unit}` : "—"}</div>
                <span className={`${styles.badge} ${styles[health.cls]}`}>{health.text}</span>
              </div>
            </div>
          );
        })}
      </div>

      <p className={styles.hint}>
        특정 센서만 “응답 없음”이면 그 센서의 배선·연결을 확인하세요.
      </p>
    </div>
  );
}
