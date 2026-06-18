"use client";

import { useState, useEffect } from "react";
import PlantCharacter from "@/components/PlantCharacter";
import SpeechBubble from "@/components/SpeechBubble";
import SensorCard from "@/components/SensorCard";
import Pill from "@/components/Pill";
import { BellIcon, DropletIcon, LedIcon } from "@/components/Icons";
import { plant } from "@/lib/data/plant";
import { getSensorReadings, getSuggestions, waterPlant, setLed, getLed, dismissSuggestion } from "@/lib/api";
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
  // 직접 제어 버튼 중복 클릭 방지(요청 진행 중 비활성화)
  const [watering, setWatering] = useState(false);
  const [ledBusy, setLedBusy] = useState(false);

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

  // 현재 LED 상태를 불러와 버튼을 복원한다. → 켜둔 채 다른 탭 갔다 와도 ON 유지.
  useEffect(() => {
    let alive = true;
    getLed()
      .then((r) => alive && setLedOn(!!r?.ledOn))
      .catch((e) => console.error("LED 상태 불러오기 실패:", e));
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

  // 직접 물 주기 — 제안과 무관하게 사용자가 언제든 펌프를 작동(suggestionId 없음).
  async function handleWater() {
    if (watering) return;
    setWatering(true);
    try {
      await waterPlant();
      setMood("happy");
      setToast("물을 주었어요. 잎이 다시 생기를 찾고 있어요!");
    } catch (e) {
      console.error("물 주기 실패:", e);
      setToast("물 주기에 실패했어요. 잠시 후 다시 시도해 주세요.");
    } finally {
      setWatering(false);
      setTimeout(() => setToast(null), 2600);
    }
  }

  // 직접 LED 켜기/끄기 — 화면 밝기는 낙관적으로 먼저 반영하고, 실패하면 되돌린다.
  async function handleToggleLed() {
    if (ledBusy) return;
    const next = !ledOn;
    setLedBusy(true);
    setLedOn(next);
    try {
      await setLed(next);
      setToast(next ? "LED를 켰어요. 한결 환해졌어요!" : "LED를 껐어요.");
    } catch (e) {
      console.error("LED 제어 실패:", e);
      setLedOn(!next); // 롤백
      setToast("LED 제어에 실패했어요. 잠시 후 다시 시도해 주세요.");
    } finally {
      setLedBusy(false);
      setTimeout(() => setToast(null), 2600);
    }
  }

  // 센서 카드(프로필 권장범위 평가). 한 번만 계산해 화면 밝기 판정에도 재사용.
  const sensorCards = readings ? evaluateSensors(readings, profile.preferences) : [];
  // 조도가 충분(또는 LED ON)하면 화면을 밝게. 데이터 로딩 전이나 조도 OK면 밝음이 기본.
  const lightCard = sensorCards.find((s) => s.key === "light");
  const screenLit = ledOn || !lightCard || lightCard.status === "good";

  return (
    <div>
      {/* 조도가 부족할 때만 화면을 어둡게 (충분하거나 LED 켜면 밝음) */}
      <div className={`${styles.dimOverlay} ${screenLit ? styles.lit : ""}`} aria-hidden="true" />

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

      {/* 직접 돌보기 — 물 주기 / LED (라즈베리파이 액추에이터 제어) */}
      <h2 className={styles.sectionTitle}>직접 돌보기</h2>
      <section className={styles.controls}>
        <button
          type="button"
          className={styles.controlBtn}
          onClick={handleWater}
          disabled={watering}
        >
          <span className={`${styles.controlIcon} ${styles.waterIcon}`} aria-hidden="true">
            <DropletIcon size={22} color="#3b86c8" />
          </span>
          <span className={styles.controlLabel}>{watering ? "물 주는 중…" : "물 주기"}</span>
        </button>

        <button
          type="button"
          className={`${styles.controlBtn} ${ledOn ? styles.controlOn : ""}`}
          onClick={handleToggleLed}
          disabled={ledBusy}
          aria-pressed={ledOn}
        >
          <span
            className={`${styles.controlIcon} ${ledOn ? styles.ledIconOn : styles.ledIcon}`}
            aria-hidden="true"
          >
            <LedIcon size={22} color={ledOn ? "#d9920a" : "var(--text-sub)"} />
          </span>
          <span className={styles.controlLabel}>{ledOn ? "LED 끄기" : "LED 켜기"}</span>
        </button>
      </section>

      {/* 센서 요약 2x2 */}
      <h2 className={styles.sectionTitle}>센서 요약</h2>
      <section className={styles.sensorGrid}>
        {sensorCards.map(({ key, ...rest }) => (
          <SensorCard key={key} {...rest} />
        ))}
      </section>
    </div>
  );
}
