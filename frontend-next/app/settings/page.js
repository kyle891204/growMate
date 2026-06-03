"use client";

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
import { useProfile } from "@/lib/hooks/useProfile";
import styles from "./settings.module.css";

function ToggleRow({ label, value }) {
  return (
    <div className={styles.row}>
      <span className={styles.rowLabel}>{label}</span>
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
  const router = useRouter();
  const { profile } = useProfile();

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
