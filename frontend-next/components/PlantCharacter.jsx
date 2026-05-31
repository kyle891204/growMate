"use client";

import { useState } from "react";
import styles from "./PlantCharacter.module.css";

/**
 * PlantCharacter
 * 레이어 분리 애니메이션: 잎은 살랑이고 화분/몸통은 고정(살짝 숨쉬기).
 *
 * 파트 파일(배경 투명 PNG, 원본과 동일한 캔버스 크기)을 아래 경로에 두면 사용됨:
 *   public/character/parts/{key}-leaves.png  (위: 잎)
 *   public/character/parts/{key}-base.png    (아래: 화분 + 몸통/얼굴)
 * 파트 파일이 없으면(로드 실패) 합쳐진 한 장 이미지로 자동 폴백한다.
 *
 * - mood: "happy" | "thirsty" | "sad" | "sleeping" | "calm"
 * - size: px 단위 정사각형 무대 크기
 * - animate: idle 모션 on/off
 */
const FULL_IMAGE = {
  happy: "/character/happy.png",
  thirsty: "/character/thirsty.png",
  sleeping: "/character/sleepy.png",
  sleepy: "/character/sleepy.png",
  calm: "/character/calm.png",
  normal: "/character/calm.png",
  sad: "/character/calm.png",
};

const PART_KEY = {
  happy: "happy",
  thirsty: "thirsty",
  sleeping: "sleepy",
  sleepy: "sleepy",
  calm: "calm",
  normal: "calm",
  sad: "calm",
};

export default function PlantCharacter({
  mood = "happy",
  size = 220,
  alt = "식물 캐릭터",
  animate = true,
}) {
  const key = PART_KEY[mood] || "main";
  const full = FULL_IMAGE[mood] || "/character/main.png";
  // 파트 파일 로드 실패 시 합쳐진 한 장으로 폴백
  const [useParts, setUseParts] = useState(true);

  if (!useParts) {
    return (
      <span className={styles.stage} style={{ width: size, height: size }}>
        <img
          src={full}
          alt={alt}
          className={`${styles.layer} ${animate ? styles.breathe : ""}`}
          draggable={false}
        />
      </span>
    );
  }

  return (
    <span className={styles.stage} style={{ width: size, height: size }}>
      {/* 아래 레이어: 화분 + 몸통/얼굴 (고정, 살짝 숨쉬기) */}
      <img
        src={`/character/parts/${key}-base.png`}
        alt={alt}
        className={`${styles.layer} ${animate ? styles.breathe : ""}`}
        draggable={false}
        onError={() => setUseParts(false)}
      />
      {/* 위 레이어: 잎 (줄기 부근을 축으로 살랑살랑) */}
      <img
        src={`/character/parts/${key}-leaves.png`}
        alt=""
        aria-hidden="true"
        className={`${styles.layer} ${animate ? styles.sway : ""}`}
        draggable={false}
      />
    </span>
  );
}
