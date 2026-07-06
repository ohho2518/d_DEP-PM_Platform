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
      <body className="min-h-full flex flex-col bg-neutral-950 text-neutral-100">
        <header className="sticky top-0 z-10 border-b border-neutral-800 bg-neutral-950/90 backdrop-blur">
          <div className="mx-auto flex w-full max-w-7xl items-center gap-6 px-6 py-3">
            <Link href="/" className="text-lg font-semibold tracking-tight">
              <span className="text-emerald-400">DEP</span>-PM
            </Link>
            <nav className="flex gap-4 text-sm text-neutral-400">
              <Link href="/" className="hover:text-neutral-100">
                Portfolio
              </Link>
              <Link href="/projects/new" className="hover:text-neutral-100">
                + New Project
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-6">{children}</main>
      </body>
    </html>
  );
}
