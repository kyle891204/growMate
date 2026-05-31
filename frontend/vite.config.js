import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 백엔드 주소: 같은 머신(Pi)에서 돌릴 때 localhost,
// 노트북에서 dev 하고 Pi에 백엔드만 있으면 Pi의 LAN IP로 교체.
const BACKEND = process.env.VITE_BACKEND || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: BACKEND,
        changeOrigin: true,
        // SSE 스트리밍 깨지지 않게
        ws: false,
        configure: (proxy) => {
          proxy.on("proxyRes", (proxyRes) => {
            // 일부 브라우저 버퍼링 방지
            proxyRes.headers["cache-control"] = "no-cache";
          });
        },
      },
    },
  },
});
