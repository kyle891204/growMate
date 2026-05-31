# GrowMate — 프론트엔드

> 사용자와 감정적으로 교감하는 **반려식물형 스마트 화분**의 모바일 웹앱 UI.
> 식물 상태와 사용자 감정을 함께 반영해, 식물이 **표정·메시지·잎 모션**으로 반응합니다.
> (라즈베리파이 기반 하드웨어 + 웹앱. 본 저장소는 **프론트엔드**입니다.)

기획·기능 명세 전체는 [`CLAUDE.md`](./CLAUDE.md) 참고.

---

## 기술 스택

- **Next.js 16 (App Router) + React 19**, JavaScript
- 스타일: **CSS Modules / 일반 CSS만 사용**
- 아이콘·차트: 외부 라이브러리 없이 **인라인 SVG**
- 외부 UI 라이브러리 미사용 (Tailwind/MUI/styled-components 등 ✕)
- 데이터: 백엔드 없이 **mock 으로 동작** (`lib/data/`) — 연동은 아래 "백엔드 연동" 참고

## 실행

```bash
npm install
npm run dev      # http://localhost:3000
```

기타 스크립트:

```bash
npm run build    # 프로덕션 빌드
npm run start    # 빌드 결과 실행
npm run lint     # ESLint
```

모바일 화면(폭 ~390px) 기준으로 중앙 정렬되며, 하단 탭바가 고정됩니다.

---

## 화면 / 라우트

| 경로 | 화면 | 설명 |
|---|---|---|
| `/` | 홈 | 식물 캐릭터, 상태 카드, 돌봄 제안 말풍선, 센서 요약 |
| `/chat` | 공감채팅 | LLM 기반 감정 공감 대화 |
| `/diary` | 일지 | 상호작용 타임라인, 오늘 요약, 주간 그래프 |
| `/settings` | 설정 | 식물 프로필, 알림/돌봄 모드, 공감채팅 설정 |

탭바는 루트 레이아웃(`app/layout.js`)에 고정되어 모든 화면에 공통 표시됩니다.

## 폴더 구조

```
app/
  layout.js          # 모바일 프레임 + 고정 TabBar
  globals.css        # 디자인 토큰 + 전역 스타일
  page.js            # 홈 (/)
  chat/page.js       # 공감채팅 (/chat)
  diary/page.js      # 일지 (/diary)
  settings/page.js   # 설정 (/settings)
components/          # TabBar, Card, Pill, Toggle, SpeechBubble, SensorCard, WeeklyChart 등
lib/
  data/              # mock 데이터 (plant, sensors, suggestions, chat, logs, settings)
  api/               # API 레이어 (백엔드 연동 지점) — 아래 참고
docs/
  api.md             # 백엔드 API 계약 문서
public/character/    # 식물 캐릭터 이미지
```

---

## 백엔드 연동

> 백엔드 담당자가 가장 먼저 볼 곳: **[`docs/api.md`](./docs/api.md)** (엔드포인트·요청/응답 형태·결정사항)

### 동작 방식: mock ↔ 실제 API 자동 전환

`lib/api/`가 모든 데이터 접근을 감쌉니다. 핵심은 **환경변수 하나**입니다:

- `NEXT_PUBLIC_API_BASE_URL`이 **없으면** → mock 모드(`lib/data/` 반환). 백엔드 없이도 전체 화면이 동작합니다.
- `NEXT_PUBLIC_API_BASE_URL`이 **있으면** → 해당 주소로 실제 `fetch` 호출.

`.env.local` 파일을 만들고 한 줄만 넣으면 실제 호출로 전환됩니다:

```bash
# .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### API 함수

`lib/api/index.js`에서 화면별 함수를 가져다 씁니다. 각 함수는 `docs/api.md`의 엔드포인트와 1:1로 대응합니다.

```js
import { getSensors, getPlantStatus, waterPlant, setLed, sendMessage } from "@/lib/api";
```

| 모듈 | 함수 | 엔드포인트 |
|---|---|---|
| `plant` | `getPlantStatus`, `getPlantProfile` | `GET /plant/status`, `GET /plant/profile` |
| `sensors` | `getSensors` | `GET /sensors` |
| `suggestions` | `getSuggestions`, `dismissSuggestion` | `GET /suggestions`, `POST /suggestions/{id}/dismiss` |
| `actions` | `waterPlant`, `setLed` | `POST /actions/water`, `POST /actions/led` |
| `chat` | `getMessages`, `sendMessage` | `GET /chat/messages`, `POST /chat` |
| `diary` | `getLogs`, `getDiarySummary`, `getWeeklyStats` | `GET /logs`, `GET /diary/summary`, `GET /stats/weekly` |
| `settings` | `getSettings`, `updateSettings` | `GET /settings`, `PATCH /settings` |

### 연동 시 남은 작업

현재 페이지들은 mock 을 직접 import 하고 상호작용을 로컬 state 로만 처리합니다. 실제 연동 위치는 코드에 **`TODO(API)` 주석**으로 표시돼 있습니다 (`app/page.js`, `app/chat/page.js`, `app/settings/page.js`). 주요 남은 작업:

1. mock import → `lib/api` 호출로 교체 (`useEffect` + 로딩/에러 상태)
2. 돌봄 제안 수락 → `waterPlant` / `setLed` 실제 호출
3. 공감채팅 → `sendMessage`(LLM 응답)로 교체
4. 설정 토글 → `updateSettings` 로 저장 (controlled 로 전환)

데이터 형태·역할 분담(원시값 vs 표시값)·미결정 항목은 모두 [`docs/api.md`](./docs/api.md)에 정리돼 있습니다.
