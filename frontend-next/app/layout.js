import "./globals.css";
import TabBar from "@/components/TabBar";

export const metadata = {
  title: "GrowMate",
  description: "사용자와 상호작용하는 반려식물 스마트 화분",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>
        <div className="app-frame">
          <main className="app-content">{children}</main>
          <TabBar />
        </div>
      </body>
    </html>
  );
}
