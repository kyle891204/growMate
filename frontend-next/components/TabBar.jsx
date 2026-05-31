"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { HomeIcon, ChatIcon, DiaryIcon, SettingsIcon } from "./Icons";
import styles from "./TabBar.module.css";

const TABS = [
  { href: "/", label: "홈", Icon: HomeIcon },
  { href: "/chat", label: "공감채팅", Icon: ChatIcon },
  { href: "/diary", label: "일지", Icon: DiaryIcon },
  { href: "/settings", label: "설정", Icon: SettingsIcon },
];

export default function TabBar() {
  const pathname = usePathname();

  return (
    <nav className={styles.tabbar} aria-label="메인 탭">
      {TABS.map(({ href, label, Icon }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            className={`${styles.tab} ${active ? styles.active : ""}`}
            aria-current={active ? "page" : undefined}
          >
            <Icon size={24} filled={active} />
            <span className={styles.label}>{label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
