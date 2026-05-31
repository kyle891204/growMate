"use client";

import Toggle from "@/components/Toggle";
import PlantCharacter from "@/components/PlantCharacter";
import { ChevronRight } from "@/components/Icons";
import {
  notifySettings,
  careSettings,
  chatSettings,
  systemMenu,
  profile,
} from "@/lib/data/settings";
import styles from "./settings.module.css";

function ToggleRow({ label, value }) {
  return (
    <div className={styles.row}>
      <span className={styles.rowLabel}>{label}</span>
      {/* TODO(API): onChange 시 updateSettings({...}) 호출해 저장. 현재는 비제어라 저장 안 됨.
          초기값도 getSettings()로 받아 controlled 로 전환 필요. lib/api/settings.js, docs/api.md §4.2 */}
      <Toggle defaultOn={value} />
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
  return (
    <div>
      <h1 className="screen-title">설정</h1>

      {/* 식물 프로필 카드 */}
      <button className={styles.profile}>
        <span className={styles.profileFace} aria-hidden="true">
          <PlantCharacter size={56} mood="happy" />
        </span>
        <div className={styles.profileBody}>
          <div className={styles.profileLabel}>내 식물 프로필</div>
          <div className={styles.profileName}>{profile.name}</div>
          <div className={styles.profileMeta}>{profile.meta}</div>
        </div>
        <ChevronRight />
      </button>

      {/* 알림 설정 */}
      <Section title="알림 설정">
        {notifySettings.map((s) => (
          <ToggleRow key={s.key} label={s.label} value={s.value} />
        ))}
      </Section>

      {/* 돌봄 모드 */}
      <Section title="돌봄 모드">
        {careSettings.map((s) => (
          <ToggleRow key={s.key} label={s.label} value={s.value} />
        ))}
      </Section>

      {/* 공감채팅 설정 */}
      <Section title="공감채팅 설정">
        {chatSettings.map((s) => {
          if (s.type === "toggle") {
            return <ToggleRow key={s.key} label={s.label} value={s.value} />;
          }
          if (s.type === "value") {
            return (
              <div key={s.key} className={styles.row}>
                <span className={styles.rowLabel}>{s.label}</span>
                <span className={styles.rowValue}>
                  {s.value}
                  <ChevronRight size={18} />
                </span>
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
          <button key={s.key} className={styles.row}>
            <span className={styles.rowLabel}>{s.label}</span>
            <ChevronRight />
          </button>
        ))}
      </Section>

      {/* 하단 버튼 */}
      <div className={styles.bottomBtns}>
        <button className={styles.logout}>로그아웃</button>
        <button className={styles.reset}>초기화</button>
      </div>
    </div>
  );
}
