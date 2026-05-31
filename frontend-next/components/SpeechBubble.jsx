import styles from "./SpeechBubble.module.css";

// 홈에서 식물이 건네는 제안 말풍선.
// tone: water(목마름/초록) | light(조도/주황)
export default function SpeechBubble({ tone = "water", children }) {
  return (
    <div className={`${styles.bubble} ${styles[tone]}`}>
      <span className={styles.tail} aria-hidden="true" />
      {children}
    </div>
  );
}
