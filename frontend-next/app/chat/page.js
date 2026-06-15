"use client";

import { useState, useRef, useEffect } from "react";
import PlantCharacter from "@/components/PlantCharacter";
import Pill from "@/components/Pill";
import { SendIcon } from "@/components/Icons";
import { promptChips } from "@/lib/data/chat";
import { streamMessage, getMessages, clearMessages } from "@/lib/api";
import { useProfile } from "@/lib/hooks/useProfile";
import styles from "./chat.module.css";

function formatTime(date) {
  let h = date.getHours();
  const m = date.getMinutes().toString().padStart(2, "0");
  const ap = h < 12 ? "오전" : "오후";
  h = h % 12 || 12;
  return `${ap} ${h}:${m}`;
}

function nowLabel() {
  return formatTime(new Date());
}

// ISO 문자열(UTC) → "오후 5:08" 라벨
function labelFromISO(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return isNaN(d) ? "" : formatTime(d);
}

// 첫 인사 (시각은 hydration mismatch 방지를 위해 비워둔다). 저장되지 않는 정적 메시지.
const GREETING = {
  id: "greeting",
  role: "plant",
  text: "안녕하세요! 오늘 하루는 어땠어요? 편하게 이야기해 주세요 🌿",
  time: "",
};

export default function ChatPage() {
  const [messages, setMessages] = useState([GREETING]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false); // 응답 스트리밍 중
  const scrollRef = useRef(null);
  const idRef = useRef(0); // 새 메시지용 로컬 카운터 (id 는 'local-N' 문자열)
  const { profile } = useProfile(); // 식물 이름/종 → 페르소나 주입

  // 마운트 시 저장된 대화 기록을 불러온다 → 페이지 이동/새로고침 후에도 유지.
  useEffect(() => {
    let alive = true;
    getMessages()
      .then((saved) => {
        if (!alive || !Array.isArray(saved) || saved.length === 0) return;
        const loaded = saved.map((m) => ({
          id: m.id,
          role: m.role,
          text: m.text,
          time: labelFromISO(m.createdAt),
        }));
        setMessages([GREETING, ...loaded]);
      })
      .catch((e) => console.error("대화 기록 불러오기 실패:", e));
    return () => {
      alive = false;
    };
  }, []);

  // 채팅 진입/새 메시지 시 항상 최근(맨 아래)으로.
  // .chatScroll 은 overflow 컨테이너가 아니라 문서 전체가 스크롤되므로 window 기준으로 내린다.
  useEffect(() => {
    const id = requestAnimationFrame(() =>
      window.scrollTo({ top: document.documentElement.scrollHeight, behavior: "auto" })
    );
    return () => cancelAnimationFrame(id);
  }, [messages]);

  async function send(text) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;

    const time = nowLabel();
    const userMsg = { id: `local-${(idRef.current += 1)}`, role: "user", text: trimmed, time };
    const plantId = `local-${(idRef.current += 1)}`;
    const plantMsg = { id: plantId, role: "plant", text: "", time };

    // 직전 대화(history)는 사용자 메시지를 추가하기 전 상태로 구성
    const history = messages.map((m) => ({ from: m.role, text: m.text }));

    setMessages((prev) => [...prev, userMsg, plantMsg]);
    setInput("");
    setBusy(true);

    // 토큰이 올 때마다 plant 메시지 텍스트에 이어붙인다 → 타이핑 효과
    const appendToken = (tok) =>
      setMessages((prev) =>
        prev.map((m) => (m.id === plantId ? { ...m, text: m.text + tok } : m))
      );

    await streamMessage(
      { message: trimmed, history, profile: { name: profile.name, species: profile.species } },
      {
        onToken: appendToken,
        onDone: (full) => {
          // 혹시 토큰 누락 시 전체 텍스트로 보정
          if (full) {
            setMessages((prev) =>
              prev.map((m) => (m.id === plantId && m.text !== full ? { ...m, text: full } : m))
            );
          }
          setBusy(false);
        },
        onError: (err) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === plantId
                ? { ...m, text: "지금은 대답하기 어려워요 ㅠ 잠시 후 다시 말 걸어줄래요?" }
                : m
            )
          );
          console.error("채팅 오류:", err);
          setBusy(false);
        },
      }
    );
  }

  function handleSubmit(e) {
    e.preventDefault();
    send(input);
  }

  // 대화 초기화: 서버 기록 삭제 + 화면을 첫 인사만 남긴 상태로 되돌린다.
  async function handleReset() {
    if (busy) return;
    if (!window.confirm("대화 기록을 모두 지울까요? 되돌릴 수 없어요.")) return;
    try {
      await clearMessages();
      idRef.current = 0;
      setMessages([GREETING]);
    } catch (e) {
      console.error("대화 초기화 실패:", e);
      window.alert("대화 초기화에 실패했어요. 잠시 후 다시 시도해 주세요.");
    }
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.titleRow}>
        <h1 className={`screen-title ${styles.title}`}>공감채팅</h1>
        <button
          type="button"
          className={styles.resetBtn}
          onClick={handleReset}
          disabled={busy}
        >
          대화 초기화
        </button>
      </div>

      {/* 상단 안내 카드 */}
      <section className={styles.introCard}>
        <span className={styles.introFace} aria-hidden="true">
          <PlantCharacter size={48} mood="happy" />
        </span>
        <div className={styles.introBody}>
          <span className={styles.modeChip}>LLM 공감 모드</span>
          <div className={styles.introTitle}>오늘 하루 어땠나요?</div>
          <p className={styles.introDesc}>언제든 이야기해 주세요. 제가 따뜻하게 들어드릴게요.</p>
        </div>
      </section>

      {/* 채팅 영역 */}
      <section className={styles.chatScroll} ref={scrollRef}>
        {messages.map((m) =>
          m.role === "plant" ? (
            <div key={m.id} className={`${styles.row} ${styles.left}`}>
              <span className={styles.miniIcon} aria-hidden="true">
                <PlantCharacter size={30} mood="happy" />
              </span>
              <div className={styles.colLeft}>
                <div className={`${styles.bubble} ${styles.plantBubble}`}>
                  {m.text || <span className={styles.typing}>…</span>}
                </div>
                {m.time && <span className={styles.time}>{m.time}</span>}
              </div>
            </div>
          ) : (
            <div key={m.id} className={`${styles.row} ${styles.right}`}>
              <div className={styles.colRight}>
                <div className={`${styles.bubble} ${styles.userBubble}`}>{m.text}</div>
                <span className={styles.time}>{m.time}</span>
              </div>
            </div>
          )
        )}
      </section>

      {/* 추천 프롬프트 칩 */}
      <div className={styles.chips}>
        {promptChips.map((c) => (
          <Pill key={c} variant="chip" onClick={() => send(c)}>
            {c}
          </Pill>
        ))}
      </div>

      {/* 입력창 */}
      <form className={styles.inputBar} onSubmit={handleSubmit}>
        <input
          className={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="오늘의 감정을 이야기해보세요"
          aria-label="메시지 입력"
          disabled={busy}
        />
        <button type="submit" className={styles.sendBtn} aria-label="전송" disabled={busy}>
          <SendIcon size={20} />
        </button>
      </form>
    </div>
  );
}
