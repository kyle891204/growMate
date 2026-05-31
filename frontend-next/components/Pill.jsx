import styles from "./Pill.module.css";

// 재사용 pill 버튼/칩.
// variant: filled(채움) | outline(외곽선) | chip(연한 초록 칩) | filter(필터칩)
export default function Pill({
  children,
  variant = "chip",
  active = false,
  className = "",
  ...rest
}) {
  return (
    <button
      type="button"
      className={`${styles.pill} ${styles[variant]} ${active ? styles.active : ""} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
