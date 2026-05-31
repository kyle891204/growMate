"use client";

import { useState } from 'react';

export default function Chat() {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    const sendMessage = async () => {
        if (!input.trim()) return;

        const newMessages = [...messages, { from: 'user', text: input }];
        setMessages(newMessages);
        setInput('');
        setIsLoading(true);

        setMessages((prev) => [...prev, { from: 'plant', text: '' }]);

        try {
            const response = await fetch('http://localhost:8000/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: input,
                    sensor: { temp: 24, humidity: 45, soil: 20 }, // 가상의 센서 데이터 (흙이 마른 상태)
                    history: newMessages
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
                            setMessages((prev) => {
                                const updated = [...prev];
                                const lastIdx = updated.length - 1;
                                updated[lastIdx].text += data.token;
                                return updated;
                            });
                        }
                    }
                }
            }
        } catch (error) {
            console.error('채팅 에러:', error);
            setMessages((prev) => [...prev, { from: 'plant', text: '앗, 연결이 끊어졌어 ㅠㅠ' }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ padding: '20px', maxWidth: '400px', background: 'white', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
            <h3 style={{ marginTop: 0, textAlign: 'center', color: '#2e7d32' }}>🌱 GrowMate 식물과 대화하기</h3>

            <div style={{ height: '300px', overflowY: 'auto', border: '1px solid #e0e0e0', padding: '10px', marginBottom: '10px', borderRadius: '8px', backgroundColor: '#fafafa' }}>
                {messages.map((msg, idx) => (
                    <div key={idx} style={{ textAlign: msg.from === 'user' ? 'right' : 'left', margin: '10px 0' }}>
            <span style={{ background: msg.from === 'user' ? '#e3f2fd' : '#e8f5e9', padding: '8px 12px', borderRadius: '15px', display: 'inline-block', maxWidth: '80%', wordBreak: 'keep-all' }}>
              {msg.text}
            </span>
                    </div>
                ))}
                {isLoading && <div style={{ fontSize: '12px', color: '#888', marginTop: '5px' }}>식물이 생각하는 중... 🌿</div>}
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="식물에게 말 걸기..."
                    style={{ flex: 1, padding: '10px', borderRadius: '8px', border: '1px solid #ccc', outline: 'none' }}
                />
                <button onClick={sendMessage} disabled={isLoading} style={{ padding: '10px 16px', borderRadius: '8px', border: 'none', backgroundColor: '#4caf50', color: 'white', cursor: 'pointer', fontWeight: 'bold' }}>
                    전송
                </button>
            </div>
        </div>
    );
}