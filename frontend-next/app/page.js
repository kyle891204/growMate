"use client";

import { useState } from "react";
import PlantCharacter from "@/components/PlantCharacter";
import SpeechBubble from "@/components/SpeechBubble";
import SensorCard from "@/components/SensorCard";
import Pill from "@/components/Pill";
import { BellIcon } from "@/components/Icons";
import { plant } from "@/lib/data/plant";
import { sensors } from "@/lib/data/sensors";
import { suggestions as initialSuggestions } from "@/lib/data/suggestions";
import styles from "./home.module.css";
// TODO(API): 위 mock import 를 lib/api 호출로 교체 — getPlantStatus / getSensors / getSuggestions
//   (useEffect + loading/error state 필요). docs/api.md §1

const TOUCH_LINES = [
  "히히, 간지러워요!",
  "와줘서 고마워요 🌱",
  "오늘도 곁에 있어줘서 든든해요.",
  "조금만 더 쓰다듬어 주세요.",
];

export default function HomePage() {
  const [suggestions, setSuggestions] = useState(initialSuggestions);
  const [mood, setMood] = useState(plant.mood);
  const [touchMsg, setTouchMsg] = useState(null);
  const [wiggle, setWiggle] = useState(false);
  const [toast, setToast] = useState(null);
  // 조명: 처음엔 어두운 상태(조도 부족). LED를 켜면 밝아진다.
  const [ledOn, setLedOn] = useState(false);

  function handleTouch() {
    const line = TOUCH_LINES[Math.floor(Math.random() * TOUCH_LINES.length)];
    setTouchMsg(line);
    setMood("happy");
    setWiggle(true);
    setTimeout(() => setWiggle(false), 600);
  }

  function resolveSuggestion(id, accepted) {
    const item = suggestions.find((s) => s.id === id);
    setSuggestions((prev) => prev.filter((s) => s.id !== id));
    if (accepted && item) {
      if (item.type === "water") {
        // TODO(API): await waterPlant(id) → 펌프 작동. lib/api/actions.js, docs/api.md §1.4
        setMood("happy");
        setToast("물을 주었어요. 잎이 다시 생기를 찾고 있어요!");
      } else {
        // TODO(API): await setLed(true) → LED ON. lib/api/actions.js, docs/api.md §1.5
        setLedOn(true);
        setToast("LED를 켰어요. 한결 환해졌어요!");
      }
      setTimeout(() => setToast(null), 2600);
    } else if (item) {
      // TODO(API): dismissSuggestion(id) → [나중에]. lib/api/suggestions.js, docs/api.md §1.6
    }
  }

  return (
    <div>
      {/* 조도 부족 시 화면이 어두컴컴해지는 오버레이 (LED 켜면 사라짐) */}
      <div className={`${styles.dimOverlay} ${ledOn ? styles.lit : ""}`} aria-hidden="true" />

      {/* 헤더 */}
      <header className={styles.header}>
        <h1 className={styles.brand}>GrowMate</h1>
        <button className={styles.bell} aria-label="알림">
          <BellIcon />
          <span className={styles.dot} />
        </button>
      </header>

      {/* 식물 영역 */}
      <section className={styles.plantArea}>
        {touchMsg && <div className={styles.touchToast}>{touchMsg}</div>}
        <button
          className={`${styles.plantBtn} ${wiggle ? styles.wiggle : ""}`}
          onClick={handleTouch}
          aria-label="식물 터치"
        >
          <PlantCharacter size={210} mood={mood} />
        </button>
        <p className={styles.touchHint}>식물을 터치해보세요!</p>
      </section>

      {/* 제안 말풍선 (식물이 필요할 때만 등장) */}
      {suggestions.length > 0 && (
        <section className={styles.suggestions}>
          {suggestions.map((s) => (
            <SpeechBubble key={s.id} tone={s.type}>
              <p className={styles.bubbleText}>{s.message}</p>
              <div className={styles.bubbleBtns}>
                <Pill variant="filled" onClick={() => resolveSuggestion(s.id, true)}>
                  {s.primary}
                </Pill>
                <Pill variant="outline" onClick={() => resolveSuggestion(s.id, false)}>
                  {s.secondary}
                </Pill>
              </div>
            </SpeechBubble>
          ))}
        </section>
      )}

      {toast && <div className={styles.actionToast}>{toast}</div>}

      {/* 식물 상태 카드 */}
      <section className={styles.statusCard}>
        <div className={styles.statusHead}>
          <span className={styles.statusFace} aria-hidden="true">
            <PlantCharacter size={46} mood={mood} />
          </span>
          <div>
            <div className={styles.statusTitle}>{plant.statusTitle}</div>
            <div className={styles.statusUpdated}>업데이트 {plant.lastUpdated}</div>
          </div>
        </div>
        <p className={styles.statusDesc}>{plant.statusDesc}</p>
      </section>

      {/* 센서 요약 2x2 */}
      <h2 className={styles.sectionTitle}>센서 요약</h2>
      <section className={styles.sensorGrid}>
        {sensors.map(({ key, ...rest }) => (
          <SensorCard key={key} {...rest} />
        ))}
      </section>
    </div>
  );
}
