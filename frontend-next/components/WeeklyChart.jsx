import styles from "./WeeklyChart.module.css";

// 라이브러리 없이 순수 SVG로 그리는 주간 변화 그래프.
// data: [{ day, soil, light }] (값 0~100)
// soil = 토양수분(실선), light = 조도(점선)
export default function WeeklyChart({ data }) {
  const W = 320;
  const H = 160;
  const padL = 36;
  const padR = 12;
  const padT = 14;
  const padB = 26;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  const n = data.length;
  const x = (i) => padL + (plotW * i) / (n - 1);
  const y = (v) => padT + plotH * (1 - v / 100);

  const toPath = (key) =>
    data.map((d, i) => `${i === 0 ? "M" : "L"} ${x(i).toFixed(1)} ${y(d[key]).toFixed(1)}`).join(" ");

  // y축 가이드: 높음(80) / 보통(50) / 낮음(20)
  const guides = [
    { label: "높음", v: 80 },
    { label: "보통", v: 50 },
    { label: "낮음", v: 20 },
  ];

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className={styles.svg} role="img" aria-label="주간 변화 그래프">
        {/* 가이드 라인 + y라벨 */}
        {guides.map((g) => (
          <g key={g.label}>
            <line x1={padL} y1={y(g.v)} x2={W - padR} y2={y(g.v)} stroke="#ecefe9" strokeWidth="1" />
            <text x={padL - 8} y={y(g.v) + 4} textAnchor="end" className={styles.axis}>
              {g.label}
            </text>
          </g>
        ))}

        {/* x축 라벨 */}
        {data.map((d, i) => (
          <text key={d.day} x={x(i)} y={H - 8} textAnchor="middle" className={styles.axis}>
            {d.day}
          </text>
        ))}

        {/* 토양수분 - 실선 */}
        <path d={toPath("soil")} fill="none" stroke="var(--green)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
        {data.map((d, i) => (
          <circle key={`s${i}`} cx={x(i)} cy={y(d.soil)} r="3" fill="var(--green)" />
        ))}

        {/* 조도 - 점선 */}
        <path
          d={toPath("light")}
          fill="none"
          stroke="var(--warn)"
          strokeWidth="2.2"
          strokeDasharray="5 4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {data.map((d, i) => (
          <circle key={`l${i}`} cx={x(i)} cy={y(d.light)} r="3" fill="var(--warn)" />
        ))}
      </svg>

      <div className={styles.legend}>
        <span className={styles.legendItem}>
          <span className={styles.lineSolid} /> 토양 수분
        </span>
        <span className={styles.legendItem}>
          <span className={styles.lineDashed} /> 조도
        </span>
      </div>
    </div>
  );
}
