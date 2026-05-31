# growMate 🌱

2026-1 한양대 피지컬컴퓨팅 5조 — 라즈베리파이 + 센서로 키우는 식물을 LLM(Google Gemini)과 채팅으로 돌보는 IoT 프로젝트.

```
┌────────────┐       ┌──────────────┐       ┌────────────────┐
│ React UI   │──────▶│ FastAPI 백엔드│──────▶│ Gemini 2.5 Flash│
│ (frontend) │ /api  │  (backend)   │ SSE   │  (cloud API)    │
└────────────┘       └──────────────┘       └────────────────┘
                              ▲
                              │ (식물 페르소나 + 센서값 system prompt)
```

## 폴더

```
growMate/
├── frontend/      React + Vite UI (식물 모니터/채팅)
├── backend/       FastAPI + Gemini API (식물 페르소나 챗봇)
└── README.md
```

## 빠른 시작 (팀원용)

### 0. clone
```bash
git clone https://github.com/Aninnom/growMate.git
cd growMate
```

### 1. Gemini API 키 발급 (1분)
- https://aistudio.google.com/apikey → "Create API key" (개인 구글 계정 권장)
- 학교 계정은 GCP 정책 때문에 안 될 수 있음
- 무료 티어: 분당 10~30 요청, 일일 약 1500 — 발표/개발 충분, 카드 등록 불필요

### 2. 백엔드 실행
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# .env 열고 GEMINI_API_KEY=AIza... 본인 키 넣기

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

확인:
```bash
curl http://localhost:8000/api/health
# {"ok": true, "model": "gemini-2.5-flash"}
```

### 3. 프론트엔드 실행 (별도 터미널)
```bash
cd frontend
npm install
npm run dev
```
브라우저 → http://localhost:5173 → 💬 탭에서 식물에게 말 걸기.

## 보안

- **`.env`는 절대 커밋 금지**. 루트 `.gitignore`에 등록되어 있음.
- 본인 API 키는 본인 컴퓨터에서만 보관. 팀원도 각자 발급해서 사용.
- 만약 키가 실수로 푸시됐다면 즉시 https://aistudio.google.com/apikey 에서 revoke 후 새 키 발급.

## 트러블슈팅

`backend/main.py`와 코드 안 주석 참고. 자주 보는 거:

| 증상 | 원인 / 해결 |
|---|---|
| `GEMINI_API_KEY 환경변수가 없음` | `backend/.env` 파일 위치/내용 확인. uvicorn을 `backend/`에서 실행했는지. |
| 응답이 한 글자만 옴 | Gemini 2.5의 thinking 토큰이 한도를 먹는 케이스. 이미 `thinking_budget=0`으로 끔. |
| 429 Too Many Requests | 분당 한도 초과. 1분 기다리거나 `MODEL=gemini-2.5-flash-lite`로. |
| CORS 오류 | `vite.config.js`의 `/api` proxy가 적용됐는지. |
| 한국어 응답이 어색함 | `backend/main.py`의 `build_system_prompt` 안 예시·규칙 조정. |

## 다음 단계 (할 일)

- 센서 실데이터 연동 (`App.jsx`의 `temp=23`, `humidity=58` 하드코딩 → Pi 센서에서 read)
- Function calling으로 LLM이 "물 줘" 인식 → 펌프 GPIO 호출
- 일지 자동 생성 (하루 대화/센서 요약 → Journal 탭)
