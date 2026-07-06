import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "DEP-PM Platform",
  description: "AI-Native Project Management — มนุษย์และ AI Agent บนบอร์ดเดียวกัน",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="th"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <header
          className="sticky top-0 z-10 border-b backdrop-blur"
          style={{ borderColor: "var(--border)", background: "rgba(255,255,255,0.85)" }}
        >
          <div className="mx-auto flex w-full max-w-7xl items-center gap-6 px-6 py-3">
            <Link href="/" className="text-lg font-bold tracking-tight" style={{ color: "var(--text)" }}>
              <span style={{ color: "var(--claude)" }}>DEP</span>-PM
              <span className="chip ml-2">AI DEV TEAM</span>
            </Link>
            <nav className="flex gap-4 text-sm" style={{ color: "var(--text2)" }}>
              <Link href="/" className="hover:opacity-70">Portfolio</Link>
              <Link href="/projects/new" className="hover:opacity-70">+ New Project</Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-6">{children}</main>
      </body>
    </html>
  );
}
