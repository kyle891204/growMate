"use client";

import { useState } from "react";
import styles from "./Toggle.module.css";

// 외부 라이브러리 없이 직접 만든 ON/OFF 스위치.
export default function Toggle({ defaultOn = false, onChange }) {
  const [on, setOn] = useState(defaultOn);

  function handle() {
    const next = !on;
    setOn(next);
    onChange?.(next);
  }

  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      className={`${styles.track} ${on ? styles.on : ""}`}
      onClick={handle}
    >
      <span className={styles.thumb} />
    </button>
  );
}
