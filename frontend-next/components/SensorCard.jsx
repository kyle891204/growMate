import { DropletIcon, ThermoIcon, HumidityIcon, SunIcon } from "./Icons";
import styles from "./SensorCard.module.css";

const ICONS = {
  droplet: DropletIcon,
  thermo: ThermoIcon,
  humidity: HumidityIcon,
  sun: SunIcon,
};

export default function SensorCard({ label, value, note, status, icon, target }) {
  const Icon = ICONS[icon] || DropletIcon;
  const color = status === "warn" ? "var(--warn)" : "var(--green)";

  return (
    <div className={styles.card}>
      <div className={styles.top}>
        <span className={styles.iconWrap} style={{ color }}>
          <Icon size={20} color="currentColor" />
        </span>
        <span className={styles.label}>{label}</span>
      </div>
      <div className={styles.value}>{value}</div>
      <div className={styles.note} style={{ color }}>{note}</div>
      {target && (
        <div className={styles.target}>권장 {target}</div>
      )}
    </div>
  );
}
