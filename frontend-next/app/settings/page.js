"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Toggle from "@/components/Toggle";
import PlantCharacter from "@/components/PlantCharacter";
import { ChevronRight } from "@/components/Icons";
import {
  notifySettings,
  careSettings,
  chatSettings,
  systemMenu,
} from "@/lib/data/settings";
import { getSettings, updateSettings } from "@/lib/api";
import { useProfile } from "@/lib/hooks/useProfile";
import styles from "./settings.module.css";

// '감정 공감 톤' 선택지 — 탭할 때마다 순환한다.
const TONE_OPTIONS = ["따뜻하게", "차분하게", "발랄하게", "담백하게"];

// 토글 한 줄. 값은 부모가 소유(controlled)하고, 바꾸면 백엔드에 저장한다.
function ToggleRow({ label, value, onChange }) {
  return (
    <div className={styles.row}>
      <span className={styles.rowLabel}>{label}</span>
      <Toggle on={!!value} onChange={onChange} />
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>{title}</h2>
      <div className={styles.group}>{children}</div>
    </section>
  );
}

export default function SettingsPage() {
  // settings: { notify:{...}, care:{...}, chat:{...} } — 백엔드 DB 값
  const [settings, setSettings] = useState(null);
  const router = useRouter();
  const { profile } = useProfile();

  useEffect(() => {
    let alive = true;
    getSettings()
      .then((s) => alive && setSettings(s))
      .catch((e) => console.error("설정 불러오기 실패:", e));
    return () => {
      alive = false;
    };
  }, []);

  // group: 'notify'|'care'|'chat', key: 항목 키, next: 새 boolean
  function handleToggle(group, key, next) {
    // 낙관적 업데이트 → 화면 즉시 반영
    setSettings((prev) => ({ ...prev, [group]: { ...prev[group], [key]: next } }));
    updateSettings({ [group]: { [key]: next } }).catch((e) => {
      console.error("설정 저장 실패:", e);
      // 실패 시 되돌리기
      setSettings((prev) => ({ ...prev, [group]: { ...prev[group], [key]: !next } }));
    });
  }

  // 값형 설정(예: 감정 공감 톤)을 리스트에서 고르면 저장.
  function setValue(group, key, value) {
    const prevValue = settings?.[group]?.[key];
    setSettings((prev) => ({ ...prev, [group]: { ...prev[group], [key]: value } }));
    updateSettings({ [group]: { [key]: value } }).catch((e) => {
      console.error("설정 저장 실패:", e);
      setSettings((prev) => ({ ...prev, [group]: { ...prev[group], [key]: prevValue } }));
    });
  }

  // 아직 로딩 전이면 기본값(false)로 보이도록 빈 객체 대비
  const notify = settings?.notify ?? {};
  const care = settings?.care ?? {};
  const chat = settings?.chat ?? {};

  return (
    <div>
      <h1 className="screen-title">설정</h1>

      {/* 식물 프로필 카드 */}
      <button className={styles.profile} onClick={() => router.push("/profile")}>
        <span className={styles.profileFace} aria-hidden="true">
          <PlantCharacter size={56} mood={profile.avatar} />
        </span>
        <div className={styles.profileBody}>
          <div className={styles.profileLabel}>내 식물 프로필</div>
          <div className={styles.profileName}>{profile.name}</div>
          <div className={styles.profileMeta}>{profile.species}{profile.adoptionDate ? ` · 입양일 ${profile.adoptionDate}` : ""}</div>
        </div>
        <ChevronRight />
      </button>

      {/* 알림 설정 */}
      <Section title="알림 설정">
        {notifySettings.map((s) => (
          <ToggleRow
            key={s.key}
            label={s.label}
            value={notify[s.key]}
            onChange={(next) => handleToggle("notify", s.key, next)}
          />
        ))}
      </Section>

      {/* 돌봄 모드 */}
      <Section title="돌봄 모드">
        {careSettings.map((s) => (
          <ToggleRow
            key={s.key}
            label={s.label}
            value={care[s.key]}
            onChange={(next) => handleToggle("care", s.key, next)}
          />
        ))}
        {/* 1회 물 주기 양 = 펌프 가동 시간(초). 1~10초, 길수록 물 많이. */}
        <div className={styles.sliderRow}>
          <div className={styles.sliderHead}>
            <span className={styles.rowLabel}>1회 물 주기 양</span>
            <span className={styles.rowValue}>{care.waterSec ?? 3}초</span>
          </div>
          <input
            className={styles.slider}
            type="range"
            min={1}
            max={10}
            step={1}
            value={care.waterSec ?? 3}
            onChange={(e) => setValue("care", "waterSec", Number(e.target.value))}
            aria-label="1회 물 주기 양(펌프 가동 시간, 초)"
          />
          <div className={styles.sliderScale}>
            <span>적게</span>
            <span>많이</span>
          </div>
        </div>
      </Section>

      {/* 공감채팅 설정 */}
      <Section title="공감채팅 설정">
        {chatSettings.map((s) => {
          if (s.type === "toggle") {
            return (
              <ToggleRow
                key={s.key}
                label={s.label}
                value={chat[s.key]}
                onChange={(next) => handleToggle("chat", s.key, next)}
              />
            );
          }
          if (s.type === "value") {
            const current = chat[s.key] ?? s.value;
            return (
              <div key={s.key} className={styles.row}>
                <span className={styles.rowLabel}>{s.label}</span>
                <select
                  className={styles.select}
                  value={current}
                  onChange={(e) => setValue("chat", s.key, e.target.value)}
                  aria-label={s.label}
                >
                  {TONE_OPTIONS.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              </div>
            );
          }
          return (
            <button key={s.key} className={styles.row}>
              <span className={styles.rowLabel}>{s.label}</span>
              <ChevronRight />
            </button>
          );
        })}
      </Section>

      {/* 연결 및 시스템 */}
      <Section title="연결 및 시스템">
        {systemMenu.map((s) => (
          <button
            key={s.key}
            className={styles.row}
            onClick={s.key === "sensorCheck" ? () => router.push("/settings/sensors") : undefined}
          >
            <span className={styles.rowLabel}>{s.label}</span>
            <ChevronRight />
          </button>
        ))}
      </Section>
    </div>
  );
}
