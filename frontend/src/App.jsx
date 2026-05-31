import { useState, useRef, useEffect } from "react";

const C = {
    bg: "#F0EBE1",
    card: "#FDFAF5",
    green: "#2E6B45",
    greenMid: "#4A8C60",
    greenLight: "#A8D5B5",
    greenPale: "#E8F5ED",
    pot: "#C4896A",
    potDark: "#A8704F",
    soil: "#6B4423",
    orange: "#E07030",
    orangePale: "#FEF0E6",
    blue: "#4A90C4",
    bluePale: "#E8F3FA",
    text: "#1E1E1E",
    muted: "#888880",
    border: "#E0D8CC",
    white: "#FDFAF5",
};

// ── Plant SVG ──────────────────────────────────────────────────
function Plant({ status, size = 1 }) {
    const happy = status === "happy";
    const thirsty = status === "thirsty";

    const lc = thirsty ? "#7DA86A" : "#3D8C55";
    const ld = thirsty ? "#5F8A50" : "#2A6B3E";

    return (
        <svg
            viewBox="0 0 200 220"
            style={{ width: 160 * size, height: 160 * size, overflow: "visible" }}
        >
            {/* Environment */}
            {!thirsty && (
                <>
                    <ellipse cx="155" cy="38" rx="22" ry="13" fill="#DDF0FF" opacity=".7" />
                    <ellipse cx="170" cy="32" rx="16" ry="12" fill="#DDF0FF" opacity=".7" />
                    <ellipse cx="40" cy="50" rx="17" ry="10" fill="#DDF0FF" opacity=".6" />
                    <ellipse cx="27" cy="44" rx="12" ry="9" fill="#DDF0FF" opacity=".6" />
                </>
            )}
            {thirsty && (
                <>
                    <ellipse cx="45" cy="45" rx="14" ry="8" fill="#F0E8D8" opacity=".6" />
                    <ellipse cx="155" cy="40" rx="12" ry="7" fill="#F0E8D8" opacity=".5" />
                </>
            )}

            {/* Pot */}
            <path d="M58 185 L70 210 L130 210 L142 185 Z" fill={C.pot} />
            <rect x="50" y="176" width="100" height="13" rx="5" fill={C.potDark} />
            <ellipse cx="100" cy="176" rx="50" ry="7" fill={C.soil} />

            {/* Leaves back */}
            <path d="M100 176 Q68 140 72 85 Q93 118 100 176" fill={ld} opacity=".65" />
            <path d="M100 176 Q132 140 128 85 Q107 118 100 176" fill={ld} opacity=".65" />

            {/* Leaves front */}
            <path d="M100 176 Q55 148 50 98 Q76 124 100 176" fill={lc} />
            <path d="M100 176 Q83 128 86 52 Q102 92 100 176" fill={ld} />
            <path d="M100 176 Q117 128 114 52 Q98 92 100 176" fill={ld} />
            <path d="M100 176 Q145 148 150 98 Q124 124 100 176" fill={lc} />

            {/* Face */}
            {happy && (
                <g>
                    <path d="M87 118 Q93 112 99 118" stroke="#1E3A26" strokeWidth="2.5" strokeLinecap="round" fill="none" />
                    <path d="M101 118 Q107 112 113 118" stroke="#1E3A26" strokeWidth="2.5" strokeLinecap="round" fill="none" />
                    <path d="M89 126 Q100 134 111 126" stroke="#1E3A26" strokeWidth="2" strokeLinecap="round" fill="none" />
                    <circle cx="85" cy="126" r="5" fill="#FFAAAA" opacity=".45" />
                    <circle cx="115" cy="126" r="5" fill="#FFAAAA" opacity=".45" />
                </g>
            )}
            {thirsty && (
                <g>
                    <ellipse cx="92" cy="117" rx="5" ry="4" fill="#1E3A26" opacity=".75" />
                    <ellipse cx="108" cy="117" rx="5" ry="4" fill="#1E3A26" opacity=".75" />
                    <ellipse cx="92" cy="125" rx="2.5" ry="3.5" fill="#7EC8E3" opacity=".8" />
                    <ellipse cx="108" cy="125" rx="2.5" ry="3.5" fill="#7EC8E3" opacity=".8" />
                    <path d="M89 131 Q100 124 111 131" stroke="#1E3A26" strokeWidth="2" strokeLinecap="round" fill="none" />
                </g>
            )}
        </svg>
    );
}

// ── Vertical gauge ─────────────────────────────────────────────
function SensorGauge({ label, icon, value, unit, pct, trackColor }) {
    return (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 5 }}>
      <span style={{ fontSize: 10, color: C.muted, fontWeight: 600, letterSpacing: ".5px" }}>
        {label}
      </span>
            <span style={{ fontSize: 17 }}>{icon}</span>
            <div
                style={{
                    width: 10, height: 72, background: "#E8E2D8", borderRadius: 6,
                    position: "relative", overflow: "hidden",
                }}
            >
                <div
                    style={{
                        position: "absolute", bottom: 0, left: 0, right: 0,
                        height: `${pct}%`, background: trackColor, borderRadius: 6,
                        transition: "height .6s ease",
                    }}
                />
            </div>
            <span style={{ fontSize: 11, fontWeight: 700, color: C.text }}>
        {value}
                <span style={{ fontSize: 9, fontWeight: 400 }}>{unit}</span>
      </span>
        </div>
    );
}

// ── Chat bubble ────────────────────────────────────────────────
function Bubble({ msg }) {
    const isUser = msg.from === "user";
    return (
        <div
            style={{
                display: "flex",
                justifyContent: isUser ? "flex-end" : "flex-start",
                gap: 7,
                alignItems: "flex-end",
                marginBottom: 8,
            }}
        >
            {!isUser && (
                <div
                    style={{
                        width: 28, height: 28, borderRadius: "50%",
                        background: C.greenLight, display: "flex",
                        alignItems: "center", justifyContent: "center",
                        fontSize: 14, flexShrink: 0,
                    }}
                >
                    🌱
                </div>
            )}
            <div>
                <div
                    style={{
                        background: isUser ? C.green : C.white,
                        color: isUser ? "#fff" : C.text,
                        padding: "9px 13px",
                        borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                        fontSize: 14,
                        maxWidth: 220,
                        lineHeight: 1.45,
                        boxShadow: "0 1px 5px rgba(0,0,0,.07)",
                    }}
                >
                    {msg.text}
                </div>
                <div
                    style={{
                        fontSize: 9, color: C.muted, marginTop: 2,
                        textAlign: isUser ? "right" : "left",
                    }}
                >
                    {msg.time}
                </div>
            </div>
        </div>
    );
}

// ── Main App ───────────────────────────────────────────────────
export default function GrowmateApp() {
    const [screen, setScreen] = useState("monitor"); // monitor | chat
    const [plantStatus, setPlantStatus] = useState("thirsty");
    const [alertDismissed, setAlertDismissed] = useState(false);
    const [chatTab, setChatTab] = useState("chat");
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState([
        { from: "plant", text: "안녕! 오늘도 잘 부탁해 🌱", time: "10:28" },
        { from: "plant", text: "요즘 좀 목이 말라... 물 줄 수 있어? 💧", time: "10:30" },
    ]);
    const [unread, setUnread] = useState(1);
    const chatEnd = useRef(null);

    const temp = 23;
    const humidity = 58;

    useEffect(() => {
        chatEnd.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, screen]);

    function now() {
        return new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
    }

    function addPlantMsg(text) {
        setMessages((p) => [...p, { from: "plant", text, time: now() }]);
        if (screen !== "chat") setUnread((n) => n + 1);
    }

    function handleWater() {
        setPlantStatus("happy");
        setAlertDismissed(true);
        setTimeout(() => addPlantMsg("물 줘서 진짜 고마워! 🌸 훨씬 기분 좋아졌어!"), 400);
    }

    function handleLater() {
        setAlertDismissed(true);
    }

    function sendMessage(text) {
        if (!text.trim()) return;
        setMessages((p) => [...p, { from: "user", text, time: now() }]);
        setInput("");

        const emojiReplies = {
            "😊": ["나도 기분 좋아! 🌿", "같이 행복하자 🌸"],
            "😢": ["왜 슬퍼? 내가 있잖아 🌱", "힘내! 응원할게 💚"],
            "❤️": ["나도 좋아해! 더 잘 자랄게 🌿", "고마워, 최고야 🌸"],
            "😴": ["같이 쉬자~ 😴", "푹 쉬어!"],
            "🔥": ["열정 뿜뿜! 🌱", "오늘도 파이팅!"],
            "🌧": ["비 좋아! 물 생각 나네 💧", "촉촉한 날이다~"],
        };
        const generic = ["고마워! 🌸", "기분이 좋아졌어!", "오늘도 잘 부탁해 😊", "같이 잘 지내자 🌿"];
        const replies = emojiReplies[text.trim()] || generic;

        setTimeout(
            () => addPlantMsg(replies[Math.floor(Math.random() * replies.length)]),
            700
        );
    }

    const showAlert = plantStatus !== "happy" && !alertDismissed;
    const alertColor = plantStatus === "thirsty" ? C.orange : C.blue;
    const alertPale = plantStatus === "thirsty" ? C.orangePale : C.bluePale;
    const alertLabel = plantStatus === "thirsty" ? "물이 필요해요 💧" : "빛이 필요해요 ☀️";
    const alertAction = plantStatus === "thirsty" ? "물 주기" : "조명 켜기";

    // ── Shared phone frame ───────────────────────────────────────
    const phone = {
        maxWidth: 390,
        margin: "0 auto",
        minHeight: "100vh",
        background: C.bg,
        display: "flex",
        flexDirection: "column",
        fontFamily: "'Georgia', serif",
        position: "relative",
        overflow: "hidden",
    };

    // ── Header ───────────────────────────────────────────────────
    const Header = () => (
        <div
            style={{
                display: "flex",
                alignItems: "center",
                padding: "13px 18px",
                background: C.white,
                borderBottom: `1px solid ${C.border}`,
            }}
        >
            {screen === "chat" ? (
                <button
                    onClick={() => { setScreen("monitor"); }}
                    style={{ background: "none", border: "none", cursor: "pointer", fontSize: 20, color: C.muted, padding: 4 }}
                >
                    ←
                </button>
            ) : (
                <button style={{ background: "none", border: "none", cursor: "pointer", fontSize: 22, color: C.text, padding: 4 }}>
                    ≡
                </button>
            )}

            <div style={{ flex: 1, textAlign: "center" }}>
        <span style={{ fontWeight: 700, fontSize: 18, color: C.green, letterSpacing: "-.3px" }}>
          Growmate 🌱
        </span>
            </div>

            {screen === "monitor" ? (
                <button
                    onClick={() => { setScreen("chat"); setUnread(0); }}
                    style={{
                        background: unread > 0 ? C.green : C.greenPale,
                        color: unread > 0 ? "#fff" : C.green,
                        border: "none", cursor: "pointer",
                        borderRadius: 20, padding: "5px 14px",
                        fontSize: 13, fontWeight: 700, position: "relative",
                    }}
                >
                    💬
                    {unread > 0 && (
                        <span
                            style={{
                                position: "absolute", top: -5, right: -5,
                                background: C.orange, color: "#fff",
                                borderRadius: "50%", width: 16, height: 16,
                                fontSize: 10, display: "flex", alignItems: "center", justifyContent: "center",
                                fontFamily: "sans-serif",
                            }}
                        >
              {unread}
            </span>
                    )}
                </button>
            ) : (
                <div style={{ width: 48 }} />
            )}
        </div>
    );

    // ── Monitor screen ───────────────────────────────────────────
    if (screen === "monitor") {
        return (
            <div style={phone}>
                <Header />

                <div style={{ flex: 1, display: "flex", gap: 12, padding: 16 }}>
                    {/* Sensor gauges */}
                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: 24,
                            justifyContent: "center",
                            alignItems: "center",
                            background: C.white,
                            borderRadius: 18,
                            padding: "14px 10px",
                            minWidth: 60,
                        }}
                    >
                        <SensorGauge
                            label="온도" icon="🌡" value={temp} unit="°C"
                            pct={((temp - 10) / 30) * 100} trackColor="#FF7043"
                        />
                        <SensorGauge
                            label="습도" icon="💧" value={humidity} unit="%"
                            pct={humidity} trackColor="#42A5F5"
                        />
                    </div>

                    {/* Plant display */}
                    <div
                        style={{
                            flex: 1,
                            background: C.white,
                            borderRadius: 18,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            minHeight: 280,
                            padding: 12,
                        }}
                    >
                        <Plant status={plantStatus} size={1.1} />
                    </div>
                </div>

                {/* Status / action bar */}
                <div style={{ padding: "0 16px 30px" }}>
                    {showAlert ? (
                        <div
                            style={{
                                background: alertPale,
                                borderRadius: 18,
                                padding: "14px 16px",
                                border: `1.5px solid ${alertColor}22`,
                            }}
                        >
                            <div style={{ display: "flex", alignItems: "center", marginBottom: 12, gap: 10 }}>
                <span style={{ fontSize: 24 }}>
                  {plantStatus === "thirsty" ? "🌵" : "🌑"}
                </span>
                                <span style={{ fontWeight: 700, color: alertColor, fontSize: 15, flex: 1 }}>
                  {alertLabel}
                </span>
                                <span style={{ fontSize: 18 }}>⚠️</span>
                            </div>
                            <div style={{ display: "flex", gap: 8 }}>
                                <button
                                    onClick={handleWater}
                                    style={{
                                        flex: 1, background: alertColor, color: "#fff",
                                        border: "none", borderRadius: 14, padding: "11px 0",
                                        fontWeight: 700, fontSize: 14, cursor: "pointer",
                                        fontFamily: "inherit",
                                    }}
                                >
                                    {alertAction}
                                </button>
                                <button
                                    onClick={handleLater}
                                    style={{
                                        flex: 1, background: "transparent", color: C.muted,
                                        border: `1px solid ${C.border}`, borderRadius: 14,
                                        padding: "11px 0", fontSize: 14, cursor: "pointer",
                                        fontFamily: "inherit",
                                    }}
                                >
                                    나중에 주기
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div
                            style={{
                                background: C.white,
                                borderRadius: 18,
                                padding: "14px 18px",
                                display: "flex",
                                alignItems: "center",
                                gap: 12,
                                boxShadow: "0 2px 10px rgba(0,0,0,.05)",
                            }}
                        >
                            <span style={{ fontSize: 26 }}>😊</span>
                            <span style={{ flex: 1, fontWeight: 700, color: C.green, fontSize: 15 }}>
                쾌적해요!
              </span>
                            <span style={{ fontSize: 20, opacity: .5 }}>⚠️</span>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // ── Chat screen ───────────────────────────────────────────────
    const journalEntries = [
        { date: "2026.05.25", note: "오늘 물 줬어 🌿 습도 65%로 상승!", mood: "😊" },
        { date: "2026.05.24", note: "빛이 부족했던 날. 조명 보충해줌 ☀️", mood: "😔" },
        { date: "2026.05.23", note: "기분 좋은 하루! 잎이 활짝 🌱", mood: "😊" },
        { date: "2026.05.22", note: "온도가 좀 높았어. 창문 열어줌", mood: "😐" },
    ];

    return (
        <div style={phone}>
            <Header />

            {/* Tabs */}
            <div
                style={{
                    display: "flex",
                    background: C.white,
                    borderBottom: `1px solid ${C.border}`,
                }}
            >
                {[
                    { key: "chat", label: "💬 채팅" },
                    { key: "journal", label: "📔 일지" },
                ].map((t) => (
                    <button
                        key={t.key}
                        onClick={() => setChatTab(t.key)}
                        style={{
                            flex: 1, padding: "11px 0", border: "none", cursor: "pointer",
                            background: "transparent",
                            fontWeight: chatTab === t.key ? 700 : 400,
                            color: chatTab === t.key ? C.green : C.muted,
                            borderBottom: chatTab === t.key ? `2.5px solid ${C.green}` : "2.5px solid transparent",
                            fontSize: 14, fontFamily: "inherit",
                        }}
                    >
                        {t.label}
                    </button>
                ))}
            </div>

            {/* Mini plant */}
            <div
                style={{
                    height: 110,
                    background: C.white,
                    margin: "12px 16px 0",
                    borderRadius: 18,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    overflow: "hidden",
                }}
            >
                <Plant status={plantStatus} size={0.7} />
            </div>

            {chatTab === "chat" ? (
                <>
                    {/* Messages */}
                    <div
                        style={{
                            flex: 1, overflowY: "auto", padding: "14px 16px",
                            display: "flex", flexDirection: "column",
                        }}
                    >
                        {messages.map((msg, i) => (
                            <Bubble key={i} msg={msg} />
                        ))}
                        <div ref={chatEnd} />
                    </div>

                    {/* Mood emoji strip */}
                    <div
                        style={{
                            background: C.white,
                            padding: "8px 16px",
                            borderTop: `1px solid ${C.border}`,
                            display: "flex",
                            justifyContent: "space-around",
                        }}
                    >
                        {["😊", "😢", "❤️", "😴", "🔥", "🌧"].map((e) => (
                            <button
                                key={e}
                                onClick={() => sendMessage(e)}
                                style={{
                                    background: "none", border: "none", cursor: "pointer",
                                    fontSize: 24, padding: "2px 6px",
                                    borderRadius: 10,
                                    transition: "transform .15s",
                                }}
                                onMouseDown={(ev) => (ev.currentTarget.style.transform = "scale(1.25)")}
                                onMouseUp={(ev) => (ev.currentTarget.style.transform = "scale(1)")}
                            >
                                {e}
                            </button>
                        ))}
                    </div>

                    {/* Text input */}
                    <div
                        style={{
                            display: "flex",
                            gap: 10,
                            padding: "10px 16px 28px",
                            background: C.white,
                        }}
                    >
                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
                            placeholder="식물에게 메시지..."
                            style={{
                                flex: 1,
                                border: `1.5px solid ${C.border}`,
                                borderRadius: 24,
                                padding: "10px 16px",
                                fontSize: 14,
                                outline: "none",
                                background: C.bg,
                                color: C.text,
                                fontFamily: "inherit",
                            }}
                        />
                        <button
                            onClick={() => sendMessage(input)}
                            style={{
                                background: C.green, color: "#fff",
                                border: "none", borderRadius: "50%",
                                width: 44, height: 44,
                                cursor: "pointer", fontSize: 18,
                                display: "flex", alignItems: "center", justifyContent: "center",
                                flexShrink: 0,
                            }}
                        >
                            ↑
                        </button>
                    </div>
                </>
            ) : (
                /* Journal */
                <div style={{ flex: 1, overflowY: "auto", padding: "14px 16px" }}>
                    <p style={{ fontSize: 12, color: C.muted, marginBottom: 12, fontFamily: "sans-serif" }}>
                        식물과 함께한 기록
                    </p>
                    {journalEntries.map((e, i) => (
                        <div
                            key={i}
                            style={{
                                background: C.white,
                                borderRadius: 14,
                                padding: "12px 14px",
                                marginBottom: 10,
                                display: "flex",
                                gap: 12,
                                alignItems: "center",
                            }}
                        >
                            <span style={{ fontSize: 28, flexShrink: 0 }}>{e.mood}</span>
                            <div>
                                <div style={{ fontSize: 11, color: C.muted, marginBottom: 3, fontFamily: "sans-serif" }}>
                                    {e.date}
                                </div>
                                <div style={{ fontSize: 14, color: C.text, lineHeight: 1.4 }}>{e.note}</div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
