"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import PlantCharacter from "@/components/PlantCharacter";
import { useProfile, DEFAULT_PROFILE } from "@/lib/hooks/useProfile";
import styles from "./profile.module.css";

const AVATARS = [
  { key: "happy",   label: "밝음"   },
  { key: "calm",    label: "평온"   },
  { key: "thirsty", label: "목마름" },
  { key: "sleepy",  label: "졸림"   },
];

const LIGHT_OPTIONS = ["낮음", "보통", "높음"];

export default function ProfilePage() {
  const router = useRouter();
  const { profile, saveProfile, loaded } = useProfile();
  const [form, setForm] = useState(DEFAULT_PROFILE);

  useEffect(() => {
    if (loaded) setForm(profile);
  }, [loaded]);

  function set(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function setPref(key, value) {
    setForm((prev) => ({
      ...prev,
      preferences: { ...prev.preferences, [key]: value },
    }));
  }

  function numChange(key) {
    return (e) => {
      const raw = e.target.value.replace(/\D/g, "");
      const stripped = raw.replace(/^0+(\d)/, "$1");
      setPref(key, stripped === "" ? 0 : Number(stripped));
    };
  }

  function handleSave() {
    saveProfile(form);
    router.back();
  }

  if (!loaded) return null;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <button className={styles.back} onClick={() => router.back()} aria-label="뒤로">
          ‹
        </button>
        <h1 className={styles.title}>식물 프로필</h1>
        <button className={styles.saveBtn} onClick={handleSave}>
          저장
        </button>
      </header>

      {/* 아바타 선택 */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>아바타</h2>
        <div className={styles.avatarRow}>
          {AVATARS.map((a) => (
            <button
              key={a.key}
              className={`${styles.avatarOption} ${form.avatar === a.key ? styles.avatarSelected : ""}`}
              onClick={() => set("avatar", a.key)}
            >
              <PlantCharacter size={56} mood={a.key} animate={false} />
              <span className={styles.avatarLabel}>{a.label}</span>
            </button>
          ))}
        </div>
      </section>

      {/* 기본 정보 */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>기본 정보</h2>
        <div className={styles.group}>
          <div className={styles.fieldRow}>
            <label className={styles.fieldLabel}>이름</label>
            <input
              className={styles.input}
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="식물 이름"
            />
          </div>
          <div className={styles.fieldRow}>
            <label className={styles.fieldLabel}>종</label>
            <input
              className={styles.input}
              value={form.species}
              onChange={(e) => set("species", e.target.value)}
              placeholder="예: 몬스테라, 고무나무"
            />
          </div>
          <div className={styles.fieldRow}>
            <label className={styles.fieldLabel}>입양일</label>
            <input
              className={`${styles.input} ${styles.inputDate}`}
              type="date"
              value={form.adoptionDate}
              onChange={(e) => set("adoptionDate", e.target.value)}
            />
          </div>
        </div>
      </section>

      {/* 환경 선호 */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>환경 선호</h2>
        <div className={styles.group}>
          {/* 온도 */}
          <div className={styles.fieldRow}>
            <label className={styles.fieldLabel}>적정 온도</label>
            <div className={styles.rangeInput}>
              <input
                className={styles.inputNum}
                type="text"
                inputMode="numeric"
                value={String(form.preferences.tempMin)}
                onFocus={(e) => e.target.select()}
                onChange={numChange("tempMin")}
              />
              <span className={styles.rangeSep}>–</span>
              <input
                className={styles.inputNum}
                type="text"
                inputMode="numeric"
                value={String(form.preferences.tempMax)}
                onFocus={(e) => e.target.select()}
                onChange={numChange("tempMax")}
              />
              <span className={styles.unit}>°C</span>
            </div>
          </div>

          {/* 습도 */}
          <div className={styles.fieldRow}>
            <label className={styles.fieldLabel}>습도</label>
            <div className={styles.rangeInput}>
              <input
                className={styles.inputNum}
                type="text"
                inputMode="numeric"
                value={String(form.preferences.humidityMin)}
                onFocus={(e) => e.target.select()}
                onChange={numChange("humidityMin")}
              />
              <span className={styles.rangeSep}>–</span>
              <input
                className={styles.inputNum}
                type="text"
                inputMode="numeric"
                value={String(form.preferences.humidityMax)}
                onFocus={(e) => e.target.select()}
                onChange={numChange("humidityMax")}
              />
              <span className={styles.unit}>%</span>
            </div>
          </div>

          {/* 토양 수분 */}
          <div className={styles.fieldRow}>
            <label className={styles.fieldLabel}>토양 수분</label>
            <div className={styles.rangeInput}>
              <input
                className={styles.inputNum}
                type="text"
                inputMode="numeric"
                value={String(form.preferences.soilMoistureMin)}
                onFocus={(e) => e.target.select()}
                onChange={numChange("soilMoistureMin")}
              />
              <span className={styles.rangeSep}>–</span>
              <input
                className={styles.inputNum}
                type="text"
                inputMode="numeric"
                value={String(form.preferences.soilMoistureMax)}
                onFocus={(e) => e.target.select()}
                onChange={numChange("soilMoistureMax")}
              />
              <span className={styles.unit}>%</span>
            </div>
          </div>

          {/* 급수 주기 */}
          <div className={styles.fieldRow}>
            <label className={styles.fieldLabel}>급수 주기</label>
            <div className={styles.rangeInput}>
              <input
                className={styles.inputNum}
                type="text"
                inputMode="numeric"
                value={String(form.preferences.wateringCycle)}
                onFocus={(e) => e.target.select()}
                onChange={numChange("wateringCycle")}
              />
              <span className={styles.unit}>일마다</span>
            </div>
          </div>

          {/* 빛 요구량 */}
          <div className={styles.fieldRow}>
            <label className={styles.fieldLabel}>빛 요구량</label>
            <div className={styles.segmentRow}>
              {LIGHT_OPTIONS.map((opt) => (
                <button
                  key={opt}
                  className={`${styles.segment} ${form.preferences.lightLevel === opt ? styles.segmentActive : ""}`}
                  onClick={() => setPref("lightLevel", opt)}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className={styles.bottomPad} />
    </div>
  );
}
