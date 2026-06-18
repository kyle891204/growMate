"use client";

import { useState, useEffect } from "react";
import Pill from "@/components/Pill";
import Card from "@/components/Card";
import WeeklyChart from "@/components/WeeklyChart";
import PlantCharacter from "@/components/PlantCharacter";
import { DropletIcon, LedIcon, ChatIcon, SunIcon } from "@/components/Icons";
import { logFilters } from "@/lib/data/logs";
import { getLogs, getDiarySummary, getWeeklyStats } from "@/lib/api";
import styles from "./diary.module.css";

const TYPE_META = {
  water: { Icon: DropletIcon, color: "var(--green)" },
  led: { Icon: LedIcon, color: "var(--warn)" },
  chat: { Icon: ChatIcon, color: "var(--green-dark)" },
  sensor: { Icon: SunIcon, color: "var(--green)" },
};

// createdAt(ISO) → "14:21" (KST). 백엔드는 naive UTC + 'Z' 로 내려준다.
function formatTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export default function DiaryPage() {
  const [filter, setFilter] = useState("all");
  const [logs, setLogs] = useState([]);
  const [summary, setSummary] = useState(null);
  const [weekly, setWeekly] = useState([]);

  // 일지/요약/주간그래프를 백엔드에서 로드 (mock 아님 — 실제 DB)
  useEffect(() => {
    let alive = true;
    getLogs("all")
      .then((d) => alive && setLogs(d))
      .catch((e) => console.error("일지 불러오기 실패:", e));
    getDiarySummary()
      .then((d) => alive && setSummary(d))
      .catch((e) => console.error("요약 불러오기 실패:", e));
    getWeeklyStats()
      .then((d) => alive && setWeekly(d))
      .catch((e) => console.error("주간 통계 불러오기 실패:", e));
    return () => {
      alive = false;
    };
  }, []);

  const visible = filter === "all" ? logs : logs.filter((l) => l.type === filter);

  return (
    <div>
      <h1 className="screen-title">일지</h1>

      {/* 오늘의 기록 요약 */}
      <Card className={styles.summary}>
        <span className={styles.summaryFace} aria-hidden="true">
          <PlantCharacter size={52} mood="happy" />
        </span>
        <div>
          <div className={styles.summaryLabel}>{summary?.title ?? "오늘의 기록"}</div>
          <div className={styles.summaryText}>{summary?.summary ?? "불러오는 중…"}</div>
          {summary?.encourage && (
            <p className={styles.summaryEncourage}>{summary.encourage}</p>
          )}
        </div>
      </Card>

      {/* 필터 칩 */}
      <div className={styles.filters}>
        {logFilters.map((f) => (
          <Pill
            key={f.key}
            variant="filter"
            active={filter === f.key}
            onClick={() => setFilter(f.key)}
          >
            {f.label}
          </Pill>
        ))}
      </div>

      {/* 타임라인 */}
      <section className={styles.timeline}>
        {visible.length === 0 && <p className={styles.empty}>해당 기록이 없어요.</p>}
        {visible.map((log, i) => {
          const meta = TYPE_META[log.type] || TYPE_META.sensor;
          const Icon = meta.Icon;
          return (
            <div key={log.id} className={styles.item}>
              <div className={styles.rail}>
                <span className={styles.node} style={{ color: meta.color }}>
                  <Icon size={16} color="currentColor" />
                </span>
                {i < visible.length - 1 && <span className={styles.line} />}
              </div>
              <div className={styles.itemBody}>
                <div className={styles.itemHead}>
                  <span className={styles.itemTime}>{formatTime(log.createdAt)}</span>
                  <span className={styles.itemTitle}>{log.title}</span>
                </div>
                <p className={styles.itemDetail}>{log.detail}</p>
              </div>
            </div>
          );
        })}
      </section>

      {/* 주간 변화 그래프 */}
      <Card className={styles.chartCard}>
        <div className={styles.chartHead}>
          <h2 className={styles.chartTitle}>주간 변화</h2>
          <span className={styles.chartFilter}>최근 7일</span>
        </div>
        <WeeklyChart data={weekly} />
      </Card>
    </div>
  );
}
