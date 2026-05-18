import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "智能数据分析系统",
  description: "自动化数据探索、可视化、机器学习建模与业务洞察",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className="h-full">
      <body className="h-full bg-[var(--c-bg)] text-[var(--c-text)]">
        {children}
      </body>
    </html>
  );
}
