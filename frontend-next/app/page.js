"use client";

import { useState, useEffect } from "react";
import PlantCharacter from "@/components/PlantCharacter";
import SpeechBubble from "@/components/SpeechBubble";
import SensorCard from "@/components/SensorCard";
import Pill from "@/components/Pill";
import { BellIcon } from "@/components/Icons";
import { plant } from "@/lib/data/plant";
import { getSensorReadings, getSuggestions, waterPlant, setLed, dismissSuggestion } from "@/lib/api";
import { evaluateSensors } from "@/lib/data/sensors";
import { useProfile } from "@/lib/hooks/useProfile";
import styles from "./home.module.css";
// 제안·센서는 백엔드에서 가져온다. 센서는 라즈베리파이가 POST 한 최신값을 주기적으로 폴링한다.
// 식물 상태(표정/문구)는 하드웨어 판정 전이라 아직 mock 을 사용한다.

const SENSOR_POLL_MS = 10000; // 10초마다 센서 새로고침

const TOUCH_LINES = [
  "히히, 간지러워요!",
  "와줘서 고마워요 🌱",
  "오늘도 곁에 있어줘서 든든해요.",
  "조금만 더 쓰다듬어 주세요.",
];

export default function HomePage() {
  const { profile } = useProfile();
  const [suggestions, setSuggestions] = useState([]);
  const [readings, setReadings] = useState(null); // 백엔드 원시 센서값
  const [mood, setMood] = useState(plant.mood);
  const [touchMsg, setTouchMsg] = useState(null);
  const [wiggle, setWiggle] = useState(false);
  const [toast, setToast] = useState(null);
  // 조명: 처음엔 어두운 상태(조도 부족). LED를 켜면 밝아진다.
  const [ledOn, setLedOn] = useState(false);

  // 활성 제안을 백엔드에서 불러온다. 처리한 제안은 서버에서 빠지므로 다시 뜨지 않는다.
  useEffect(() => {
    let alive = true;
    getSuggestions()
      .then((list) => alive && setSuggestions(list))
      .catch((e) => console.error("제안 불러오기 실패:", e));
    return () => {
      alive = false;
    };
  }, []);

  // 센서 원시값을 주기적으로 폴링 → 라즈베리파이가 보낸 최신값이 홈에 반영된다.
  // 상태/권장범위 판정은 식물 프로필의 선호(profile.preferences)로 화면에서 계산한다.
  useEffect(() => {
    let alive = true;
    const load = () =>
      getSensorReadings()
        .then((r) => alive && setReadings(r))
        .catch((e) => console.error("센서 불러오기 실패:", e));
    load();
    const timer = setInterval(load, SENSOR_POLL_MS);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  function handleTouch() {
    const line = TOUCH_LINES[Math.floor(Math.random() * TOUCH_LINES.length)];
    setTouchMsg(line);
    setMood("happy");
    setWiggle(true);
    setTimeout(() => setWiggle(false), 600);
  }

  async function resolveSuggestion(id, accepted) {
    const item = suggestions.find((s) => s.id === id);
    if (!item) return;
    // 낙관적으로 먼저 화면에서 제거 (서버 저장은 비동기로 진행)
    setSuggestions((prev) => prev.filter((s) => s.id !== id));
    try {
      if (accepted) {
        if (item.type === "water") {
          await waterPlant(id); // 펌프 작동 + 제안 처리완료 저장
          setMood("happy");
          setToast("물을 주었어요. 잎이 다시 생기를 찾고 있어요!");
        } else {
          await setLed(true, id); // LED ON + 제안 처리완료 저장
          setLedOn(true);
          setToast("LED를 켰어요. 한결 환해졌어요!");
        }
        setTimeout(() => setToast(null), 2600);
      } else {
        await dismissSuggestion(id); // [나중에] — 숨김 저장
      }
    } catch (e) {
      console.error("제안 처리 실패:", e);
      // 실패 시 목록 복구
      setSuggestions((prev) => (prev.some((s) => s.id === id) ? prev : [...prev, item]));
      setToast("처리 중 문제가 생겼어요. 잠시 후 다시 시도해 주세요.");
      setTimeout(() => setToast(null), 2600);
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
        <div className={`${styles.plantGlow} ${wiggle ? styles.wiggle : ""}`}>
          <div className={styles.plantGlowBg} aria-hidden="true" />
          <button
            className={styles.plantBtn}
            onClick={handleTouch}
            aria-label="식물 터치"
          >
            <PlantCharacter size={190} mood={mood} />
          </button>
        </div>

        {/* 식물 이름 · 종 · 입양일 */}
        <div className={styles.plantIdentity}>
          <p className={styles.plantName}>{profile.name}</p>
          <div className={styles.plantMeta}>
            <span className={styles.speciesBadge}>{profile.species}</span>
            {profile.adoptionDate && (
              <span className={styles.adoptionDays}>
                · {Math.floor((Date.now() - new Date(profile.adoptionDate)) / 86400000)}일째 함께
              </span>
            )}
          </div>
        </div>

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

      {/* 식물 프로필 + 상태 카드 */}
      <section className={styles.statusCard}>
        <div className={styles.statusHead}>
          <span className={styles.statusFace} aria-hidden="true">
            <PlantCharacter size={46} mood={mood} />
          </span>
          <div className={styles.statusInfo}>
            <div className={styles.statusTitle}>{plant.statusTitle}</div>
            <div className={styles.statusUpdated}>업데이트 {plant.lastUpdated}</div>
          </div>
        </div>
        <p className={styles.statusDesc}>{plant.statusDesc}</p>
      </section>

      {/* 센서 요약 2x2 */}
      <h2 className={styles.sectionTitle}>센서 요약</h2>
      <section className={styles.sensorGrid}>
        {(readings ? evaluateSensors(readings, profile.preferences) : []).map(({ key, ...rest }) => (
          <SensorCard key={key} {...rest} />
        ))}
      </section>
    </div>
  );
}
