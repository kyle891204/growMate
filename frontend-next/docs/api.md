# GrowMate API 계약 (프론트 → 백엔드)

> 이 문서는 **현재 프론트엔드가 사용하는 mock 데이터(`lib/data/*.js`)를 기준으로** 백엔드가 제공해야 할 엔드포인트와 데이터 형태를 정리한 것입니다.
> 프론트는 지금 백엔드 없이 로컬 state로만 동작하므로, 아래 엔드포인트로 mock을 교체하는 것이 연동 목표입니다.
>
> - 작성 기준일: 2026-05-31
> - 프론트 스택: Next.js (App Router) + React, mock 데이터는 `lib/data/`
> - **결정이 필요한 항목**은 각 섹션과 맨 아래 "남은 결정사항"에 ⚠️로 표시했습니다.

---

## 0. 공통 사항

### 0.1 Base URL / 환경변수
- 프론트는 `NEXT_PUBLIC_API_BASE_URL` 환경변수로 API 베이스 주소를 읽습니다. (예: `http://raspberrypi.local:8000` 또는 `http://localhost:8000`)
- 모든 경로는 이 베이스 뒤에 붙습니다. (예: `GET {BASE}/sensors`)

### 0.2 데이터 형식 규칙 (중요)
연동 충돌을 막기 위해 **역할을 다음과 같이 나눕니다.**

| 항목 | 담당 | 설명 |
|---|---|---|
| 원시 측정값 (숫자) | **백엔드** | 센서값은 `24`, `24.6`처럼 **숫자**로 준다. `"24%"` 같은 문자열 X |
| 상태 판정 (`good`/`warn`) | **백엔드** | 임계값 판정은 식물 종류·기준을 아는 백엔드가 한다 |
| 시각 (timestamp) | **백엔드** | 항상 ISO 8601 (KST 오프셋 포함). 예: `2026-05-31T17:05:00+09:00` |
| 단위 표시 / 한글 라벨 / 한글 안내문구 | **프론트** | `"토양 수분"`, `"건조"`, `"방금 전"`, `"14:21"` 등 화면 표시는 프론트가 가공 |
| 제안/말풍선/채팅칩 UI 문구 | **프론트** | UI 카피는 프론트 소유. 백엔드는 "어떤 종류가 활성인지"만 알려줌 |

→ 즉 **백엔드는 "데이터 + 상태값"을, 프론트는 "한글 표현"을** 담당합니다.

### 0.3 공통 응답/에러 포맷
성공:
```json
{ "ok": true, "data": { ... } }
```
> 또는 데이터 본문을 바로 반환해도 됩니다. (팀 합의 후 한쪽으로 통일 ⚠️)

에러:
```json
{ "ok": false, "error": { "code": "SENSOR_UNAVAILABLE", "message": "센서에 연결할 수 없어요." } }
```
- HTTP 상태코드도 함께 사용 (400/401/404/500 등)
- 프론트는 `error.message`를 토스트/안내로 보여줍니다.

### 0.4 사용자 / 기기 식별 ⚠️
현재 프론트에는 인증/기기 식별 개념이 없습니다. 아래 중 택1 필요:
- (MVP) 화분 1대 = 서버 1대로 보고 인증 없이 진행
- (확장) `deviceId` 또는 토큰을 헤더(`Authorization`)로 전달
> 결정되면 모든 요청 헤더 규칙을 여기에 추가합니다.

### 0.5 실시간 갱신 전략 ⚠️
센서·식물상태·제안은 계속 바뀝니다. MVP 권장안:
- **폴링**: 프론트가 `GET /sensors`, `GET /plant/status`, `GET /suggestions`를 일정 주기(예: 10초)로 호출
- (확장) WebSocket / SSE로 푸시
> MVP는 폴링으로 가정하고 작성했습니다.

---

## 1. 홈 화면 (`/`)

연동 대상 파일: `app/page.js`, `lib/data/plant.js`, `lib/data/sensors.js`, `lib/data/suggestions.js`

### 1.1 `GET /plant/status` — 식물 현재 상태
홈 상단 캐릭터 표정 + 상태 카드에 사용.

응답:
```json
{
  "mood": "thirsty",
  "statusTitle": "조금 목이 마른 것 같아요",
  "statusDesc": "흙이 건조해졌어요. 물을 주면 다시 싱그럽게 자랄 거예요!",
  "updatedAt": "2026-05-31T17:05:00+09:00"
}
```
- `mood`: `happy | thirsty | sleepy` (캐릭터 표정 enum)
- `updatedAt`: 프론트가 `"방금 전"` 등으로 변환
- ⚠️ `statusTitle/statusDesc`를 **백엔드가 생성**할지, 프론트가 `mood`로 매핑할지 결정 필요. (현재 문서는 백엔드 생성 가정)

### 1.2 `GET /sensors` — 센서 요약
홈 하단 2x2 센서 카드.

응답:
```json
{
  "updatedAt": "2026-05-31T17:05:00+09:00",
  "sensors": [
    { "key": "soil",  "value": 24,   "unit": "%",   "status": "warn" },
    { "key": "temp",  "value": 24.6, "unit": "°C",  "status": "good" },
    { "key": "humid", "value": 58,   "unit": "%",   "status": "good" },
    { "key": "light", "value": 520,  "unit": "lux", "status": "warn" }
  ]
}
```
- `key`: `soil | temp | humid | light` (고정)
- `status`: `good | warn` (필요시 `critical` 추가 ⚠️)
- 한글 라벨(`"토양 수분"`)·안내문(`"건조"`)·아이콘은 **프론트가 `key`/`status`로 매핑**

### 1.3 `GET /suggestions` — 식물의 돌봄 제안
"조금 목말라요. 물을 줄까요?" 같은 말풍선. 센서 상태에 따라 백엔드가 활성 제안을 판단.

응답:
```json
{
  "suggestions": [
    { "id": "water-20260531-1705", "type": "water" },
    { "id": "light-20260531-1705", "type": "light" }
  ]
}
```
- `type`: `water | light`
- `id`: dismiss/action에서 참조할 고유값
- 말풍선 문구(`"조금 목말라요..."`)·버튼 라벨(`"물 주기"`)은 **프론트가 `type`별로 소유**
- 활성 제안이 없으면 빈 배열

### 1.4 `POST /actions/water` — 물 주기 실행 (펌프 작동)
사용자가 말풍선에서 `[물 주기]`를 누를 때. **GrowMate의 핵심: 실제 하드웨어 제어로 연결되는 지점.**

요청:
```json
{ "suggestionId": "water-20260531-1705" }
```
응답:
```json
{
  "ok": true,
  "log": { "id": 5, "type": "water", "title": "물 주기 완료", "detail": "사용자 직접 선택", "createdAt": "2026-05-31T17:06:00+09:00" },
  "plant": { "mood": "happy" }
}
```
- 펌프 작동 후, 새로 생성된 일지 로그와 변경된 식물 상태를 함께 반환하면 프론트가 즉시 반영

### 1.5 `POST /actions/led` — LED 제어
사용자가 `[LED 켜기]`를 누르거나 설정에서 제어.

요청:
```json
{ "on": true }
```
응답:
```json
{
  "ok": true,
  "ledOn": true,
  "log": { "id": 6, "type": "led", "title": "LED 켜짐", "detail": "사용자 직접 선택", "createdAt": "2026-05-31T17:07:00+09:00" }
}
```

### 1.6 `POST /suggestions/{id}/dismiss` — 제안 미루기 ([나중에])
요청 본문 없음.
응답:
```json
{ "ok": true }
```

---

## 2. 공감채팅 화면 (`/chat`)

연동 대상 파일: `app/chat/page.js`, `lib/data/chat.js`
> 현재 `getPlantReply()`는 키워드 매칭 mock입니다. 아래 `POST /chat`(LLM 호출)로 교체합니다.

### 2.1 `GET /chat/messages` — 대화 기록 조회
쿼리: `?limit=50&before=<messageId|ISO>` (페이지네이션, 선택)

응답:
```json
{
  "messages": [
    { "id": "m1", "role": "user",  "text": "오늘 과제도 많고 너무 지쳤어.", "createdAt": "2026-05-31T17:08:00+09:00" },
    { "id": "m2", "role": "plant", "text": "오늘 정말 고생 많았어요. ...", "createdAt": "2026-05-31T17:08:02+09:00" }
  ]
}
```
- `role`: `user | plant`
- 시각 표시(`"오후 5:08"`)는 프론트가 `createdAt`으로 변환

### 2.2 `POST /chat` — 메시지 전송 + 식물(LLM) 응답
요청:
```json
{ "text": "괜히 마음이 불안해." }
```
응답:
```json
{
  "userMessage": { "id": "m3", "role": "user",  "text": "괜히 마음이 불안해.", "createdAt": "2026-05-31T17:10:00+09:00" },
  "reply":       { "id": "m4", "role": "plant", "text": "그럴 수 있어요. 지금처럼 ...", "createdAt": "2026-05-31T17:10:01+09:00" }
}
```
- ⚠️ **스트리밍 여부 결정**: MVP는 단발 JSON 응답. 추후 SSE 스트리밍 고려 가능
- `tone`(감정 공감 톤) 등 설정값을 LLM 프롬프트에 반영 → 설정은 `GET /settings`의 `chat.tone` 참고

---

## 3. 일지 화면 (`/diary`)

연동 대상 파일: `app/diary/page.js`, `lib/data/logs.js`

### 3.1 `GET /logs` — 상호작용 타임라인
쿼리:
- `type`: `all | water | led | chat | sensor` (기본 `all`)
- `from`, `to`: ISO 날짜 범위 (선택)
- `limit`: 개수 (선택)

응답:
```json
{
  "logs": [
    { "id": 1, "type": "water",  "title": "물 주기 완료", "detail": "사용자 직접 선택",            "createdAt": "2026-05-31T14:21:00+09:00" },
    { "id": 2, "type": "led",    "title": "LED 켜짐",     "detail": "조도 부족으로 보조 조명 작동", "createdAt": "2026-05-31T15:00:00+09:00" },
    { "id": 3, "type": "chat",   "title": "기분 대화",     "detail": "사용자 감정: 지침 / 식물 반응: 위로 메시지", "createdAt": "2026-05-31T17:10:00+09:00" },
    { "id": 4, "type": "sensor", "title": "상태 안정",     "detail": "토양 수분 정상, 조도 정상",     "createdAt": "2026-05-31T18:30:00+09:00" }
  ]
}
```
- `type`: `water | led | chat | sensor`
- 시각(`"14:21"`)은 프론트가 `createdAt`으로 변환
- 필터링은 서버(`?type=`) 또는 프론트 둘 다 가능. (현재 프론트가 클라이언트 필터링 중)

### 3.2 `GET /diary/summary` — 오늘의 기록 요약
쿼리: `?date=2026-05-31` (선택, 기본 오늘)

응답(권장: 구조화된 수치):
```json
{
  "date": "2026-05-31",
  "counts": { "water": 1, "led": 2, "chat": 3 },
  "stable": true
}
```
- 프론트가 이 수치로 `"오늘 물 주기 1회, LED 2회, 상태 안정"` 문장을 구성
- ⚠️ 대안: 백엔드가 `summary`/`encourage` 문장을 통째로 내려줘도 됨 (현재 mock은 문장형)

### 3.3 `GET /stats/weekly` — 주간 변화 그래프
쿼리: `?days=7&metrics=soil,light`

응답(권장: 원시 일별 평균값):
```json
{
  "points": [
    { "date": "2026-05-25", "soil": 62, "light": 480 },
    { "date": "2026-05-26", "soil": 55, "light": 600 }
  ]
}
```
- `soil`: % , `light`: lux 등 **원시 단위**로 반환 → 프론트가 차트용으로 정규화
- ⚠️ 현재 mock(`weekly`)은 0~100 정규화값을 씀. **원시값 vs 정규화값** 중 어느 쪽을 줄지 결정 필요 (문서는 원시값 권장)

---

## 4. 설정 화면 (`/settings`)

연동 대상 파일: `app/settings/page.js`, `lib/data/settings.js`
> 현재 토글은 `defaultOn`만 받는 비제어 컴포넌트라 저장이 안 됩니다. 아래 GET/PATCH로 연동 필요.

### 4.1 `GET /settings` — 전체 설정 조회
응답:
```json
{
  "notify": { "water": true, "light": false, "chat": true },
  "care":   { "autoProtect": true, "ledAuto": true, "showSuggest": false },
  "chat":   { "saveHistory": true, "tone": "warm", "nickname": "" }
}
```
- `notify`: 알림 설정 (물 주기 / 조도 부족 / 공감채팅)
- `care`: 돌봄 모드 (자동 보호 / LED 자동 보조 / 제안 메시지 표시)
- `chat.tone`: 감정 공감 톤. 저장은 키값(`warm` 등), 화면 표시(`"따뜻하게"`)는 프론트가 매핑 ⚠️ tone enum 목록 합의 필요
- `chat.nickname`: 식물 별명 (빈 문자열 가능)

### 4.2 `PATCH /settings` — 설정 변경
요청(부분 업데이트):
```json
{ "notify": { "light": true } }
```
응답: 변경 후 전체 설정 객체(4.1과 동일 형태)

### 4.3 `GET /plant/profile` — 식물 프로필
응답:
```json
{ "name": "그로우메이트", "species": "몬스테라", "connection": "ok" }
```
- `connection`: `ok | disconnected` (화면 표시 `"연결 정상"`은 프론트 매핑)

### 4.4 기타 (하단 버튼 / 시스템) ⚠️ 우선순위 낮음
- `POST /auth/logout` — 로그아웃 (인증 도입 시)
- `POST /system/reset` — 초기화
- `GET /system/status` — 센서 상태 / Wi-Fi / 장치 정보 (설정 "연결 및 시스템" 메뉴)
> 인증 모델이 정해진 뒤 구체화합니다.

---

## 5. 데이터 타입 / Enum 정리

| 이름 | 값 | 사용처 |
|---|---|---|
| `mood` | `happy` `thirsty` `sleepy` | 캐릭터 표정 (`plant.mood`) |
| 센서 `key` | `soil` `temp` `humid` `light` | 센서 카드 |
| 센서 `status` | `good` `warn` (`critical`?) | 센서 판정 |
| 제안 `type` | `water` `light` | 홈 말풍선 |
| 채팅 `role` | `user` `plant` | 대화 메시지 |
| 로그 `type` | `water` `led` `chat` `sensor` | 일지 타임라인 |
| `connection` | `ok` `disconnected` | 프로필 연결상태 |
| `tone` | `warm` (…목록 미정) | 공감채팅 톤 |

---

## 6. 엔드포인트 한눈에 보기

| Method | Path | 용도 | 화면 |
|---|---|---|---|
| GET | `/plant/status` | 식물 상태/표정 | 홈 |
| GET | `/sensors` | 센서 요약 | 홈 |
| GET | `/suggestions` | 돌봄 제안 목록 | 홈 |
| POST | `/actions/water` | 물 주기(펌프) 실행 | 홈 |
| POST | `/actions/led` | LED ON/OFF | 홈/설정 |
| POST | `/suggestions/{id}/dismiss` | 제안 미루기 | 홈 |
| GET | `/chat/messages` | 대화 기록 | 채팅 |
| POST | `/chat` | 메시지 전송 + LLM 응답 | 채팅 |
| GET | `/logs` | 일지 타임라인 | 일지 |
| GET | `/diary/summary` | 오늘 요약 | 일지 |
| GET | `/stats/weekly` | 주간 그래프 | 일지 |
| GET | `/settings` | 설정 조회 | 설정 |
| PATCH | `/settings` | 설정 변경 | 설정 |
| GET | `/plant/profile` | 식물 프로필 | 설정 |
| POST | `/auth/logout` | 로그아웃 | 설정 |
| POST | `/system/reset` | 초기화 | 설정 |

---

## 7. 남은 결정사항 (백엔드와 합의 필요) ⚠️

1. **응답 래핑**: `{ ok, data }` 통일 vs 본문 직접 반환 — 한쪽으로 통일
2. **인증/기기 식별**: 무인증(화분 1대) vs `deviceId`/토큰 헤더
3. **실시간**: 폴링 주기 vs WebSocket/SSE
4. **식물 상태 문구**: `statusTitle/statusDesc`를 백엔드 생성 vs 프론트가 `mood`로 매핑
5. **제안 문구**: 프론트가 `type`별 소유(권장) vs 백엔드가 message 제공
6. **주간 그래프 값**: 원시 단위(권장) vs 0~100 정규화
7. **오늘 요약**: 수치(`counts`) 반환(권장) vs 문장 반환
8. **센서 status 단계**: `good/warn` 2단계 vs `critical` 포함 3단계
9. **채팅 응답**: 단발 JSON vs SSE 스트리밍
10. **tone enum 목록**: `warm` 외 어떤 값들?
