// 모든 아이콘은 외부 라이브러리 없이 인라인 SVG로 직접 그린다.
// currentColor를 사용해 부모의 color로 색이 결정되게 한다.

export function HomeIcon({ size = 24, filled = false }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 11.2 12 4.5l8 6.7V19a1.5 1.5 0 0 1-1.5 1.5h-3.2v-5h-6.6v5H5.5A1.5 1.5 0 0 1 4 19v-7.8Z"
        fill={filled ? "currentColor" : "none"}
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function ChatIcon({ size = 24, filled = false }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v7A2.5 2.5 0 0 1 17.5 16H9l-4 3.5V16H6.5"
        fill={filled ? "currentColor" : "none"}
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function DiaryIcon({ size = 24, filled = false }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M6 3.5h11A1.5 1.5 0 0 1 18.5 5v15.5l-3-2-3 2-3-2-3 2V5A1.5 1.5 0 0 1 6 3.5Z"
        fill={filled ? "currentColor" : "none"}
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
      <path d="M9 8h6M9 11.5h6" stroke={filled ? "#fff" : "currentColor"} strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

export function SettingsIcon({ size = 24, filled = false }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="3" fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.7" />
      <path
        d="M12 2.8v2.4M12 18.8v2.4M21.2 12h-2.4M5.2 12H2.8M18.5 5.5l-1.7 1.7M7.2 16.8l-1.7 1.7M18.5 18.5l-1.7-1.7M7.2 7.2 5.5 5.5"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function BellIcon({ size = 22 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M6 9.5a6 6 0 0 1 12 0c0 4 1.2 5.5 2 6.5H4c.8-1 2-2.5 2-6.5Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
      <path d="M9.8 19a2.4 2.4 0 0 0 4.4 0" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

export function DropletIcon({ size = 22, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 3.5s6 6.3 6 10.2A6 6 0 0 1 6 13.7C6 9.8 12 3.5 12 3.5Z"
        fill="none"
        stroke={color}
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function ThermoIcon({ size = 22, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M10 13.5V6a2 2 0 0 1 4 0v7.5a3.5 3.5 0 1 1-4 0Z"
        stroke={color}
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="16.5" r="1.4" fill={color} />
    </svg>
  );
}

export function HumidityIcon({ size = 22, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3.5s6 6.3 6 10.2A6 6 0 0 1 6 13.7C6 9.8 12 3.5 12 3.5Z" stroke={color} strokeWidth="1.7" strokeLinejoin="round" />
      <path d="M9.5 13.8a2.6 2.6 0 0 0 2.6 2.6" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export function SunIcon({ size = 22, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="4" stroke={color} strokeWidth="1.7" />
      <path
        d="M12 2.6v2.2M12 19.2v2.2M21.4 12h-2.2M4.8 12H2.6M18.4 5.6l-1.5 1.5M7.1 16.9l-1.5 1.5M18.4 18.4l-1.5-1.5M7.1 7.1 5.6 5.6"
        stroke={color}
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function LedIcon({ size = 22, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M9 17h6M9.5 20h5M12 3.5a6 6 0 0 1 3.6 10.8c-.5.4-.8 1-.8 1.6H9.2c0-.6-.3-1.2-.8-1.6A6 6 0 0 1 12 3.5Z"
        stroke={color}
        strokeWidth="1.7"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function SendIcon({ size = 20, color = "#fff" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 12 20 4l-6 16-3.2-6.4L4 12Z" fill={color} stroke={color} strokeWidth="1.4" strokeLinejoin="round" />
    </svg>
  );
}

export function ChevronRight({ size = 20, color = "var(--text-sub)" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="m9.5 6 6 6-6 6" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
