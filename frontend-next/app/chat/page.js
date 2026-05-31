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

async function send(text) {
    const trimmed = text.trim();
    if (!trimmed) return;

    // 1. 유저 메시지 화면에 띄우기 (원본 유지)
    const time = nowLabel();
    const userMsg = { id: (idRef.current += 1), role: "user", text: trimmed, time };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    // 2. 식물 메시지 '빈 칸' 미리 만들기 (여기서 plantId를 확실하게 선언!)
    const plantId = (idRef.current += 1);
    const plantMsg = {
        id: plantId,
        role: "plant",
        text: "",
        time,
    };
    setMessages((prev) => [...prev, plantMsg]);

    // 3. 파이썬 서버와 통신 시작
    try {
        const response = await fetch('http://localhost:8000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: trimmed,
                sensor: { temp: 24, humidity: 45, soil: 20 },
                history: messages.map(m => ({ from: m.role, text: m.text }))
            }),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.replace('data: ', '').trim();
                    if (!dataStr) continue;

                    const data = JSON.parse(dataStr);
                    if (data.done) break;

                    if (data.token) {
                        // 위에서 꽉 잡아둔 plantId를 여기서 안전하게 사용!
                        setMessages((prev) =>
                            prev.map((msg) =>
                                msg.id === plantId
                                    ? { ...msg, text: msg.text + data.token }
                                    : msg
                            )
                        );
                    }
                }
            }
        }
    } catch (error) {
        console.error('LLM API 에러:', error);
        setMessages((prev) =>
            prev.map((msg) =>
                msg.id === plantId
                    ? { ...msg, text: "서버와 연결이 끊어졌어요 ㅠㅠ" }
                    : msg
            )
        );
    }
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
