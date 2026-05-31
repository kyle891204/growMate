// GrowMate API 클라이언트 (공통 fetch 래퍼)
// 계약 문서: docs/api.md
//
// 동작 모드:
// - NEXT_PUBLIC_API_BASE_URL 가 설정돼 있으면 실제 백엔드를 호출합니다.
// - 설정이 없으면(USE_MOCK = true) lib/data/ 의 mock 을 반환해 백엔드 없이도 화면이 동작합니다.
//   → 백엔드 담당자는 .env.local 에 NEXT_PUBLIC_API_BASE_URL 만 넣으면 실제 호출로 전환됩니다.
//     예) NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";
export const USE_MOCK = !API_BASE;

export class ApiError extends Error {
  constructor(message, status, code) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

// 모든 실제 호출의 진입점. docs/api.md §0.3 의 응답/에러 포맷을 따른다.
export async function apiFetch(path, { method = "GET", body, headers, ...rest } = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json", ...headers },
    body: body != null ? JSON.stringify(body) : undefined,
    ...rest,
  });

  let payload = null;
  try {
    payload = await res.json();
  } catch {
    // 본문이 비어 있을 수 있음 (예: 204)
  }

  if (!res.ok) {
    const err = payload?.error;
    throw new ApiError(err?.message || `요청 실패 (${res.status})`, res.status, err?.code);
  }

  // { ok, data } 래핑을 쓰면 data 를, 아니면 본문을 그대로 반환 (docs/api.md §0.3 결정사항)
  return payload?.data ?? payload;
}

// mock 모드에서 비동기 호출처럼 보이도록 약간의 지연을 준다.
export function mockDelay(value, ms = 150) {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}
