"use client";

import { useState, useRef, useEffect } from "react";
import PlantCharacter from "@/components/PlantCharacter";
import Pill from "@/components/Pill";
import { SendIcon } from "@/components/Icons";
import { initialMessages, promptChips, getPlantReply } from "@/lib/data/chat";
import styles from "./chat.module.css";

function nowLabel() {
  const d = new Date();
  let h = d.getHours();
  const m = d.getMinutes().toString().padStart(2, "0");
  const ap = h < 12 ? "오전" : "오후";
  h = h % 12 || 12;
  return `${ap} ${h}:${m}`;
}

export default function ChatPage() {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState("");
  const scrollRef = useRef(null);
  // 새 메시지 고유 id 카운터 (Date.now 대신 — 렌더 순수성 유지). 초기 mock id 와 겹치지 않게 시작값을 둠
  const idRef = useRef(initialMessages.length);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  function send(text) {
    const trimmed = text.trim();
    if (!trimmed) return;
    // TODO(API): sendMessage(trimmed) 호출 → 백엔드 LLM 응답(reply)으로 교체.
    //   getPlantReply(키워드 mock) 대신 사용. lib/api/chat.js, docs/api.md §2.2
    const time = nowLabel();
    const userMsg = { id: (idRef.current += 1), role: "user", text: trimmed, time };
    const plantMsg = {
      id: (idRef.current += 1),
      role: "plant",
      text: getPlantReply(trimmed),
      time,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    // 식물의 공감 응답을 약간의 지연 후 추가 (대화처럼 보이게)
    setTimeout(() => setMessages((prev) => [...prev, plantMsg]), 500);
  }

  function handleSubmit(e) {
    e.preventDefault();
    send(input);
  }

  return (
    <div className={styles.wrap}>
      <h1 className="screen-title">공감채팅</h1>

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
                <div className={`${styles.bubble} ${styles.plantBubble}`}>{m.text}</div>
                <span className={styles.time}>{m.time}</span>
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
        />
        <button type="submit" className={styles.sendBtn} aria-label="전송">
          <SendIcon size={20} />
        </button>
      </form>
    </div>
  );
}
