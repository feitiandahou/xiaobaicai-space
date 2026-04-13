import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/layout/Navbar";
import { AmbientBackground } from "@/components/layout/AmbientBackground";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Xiaobaicai Space - Beautiful Personal Blog",
  description: "A minimalist, artistic personal space built with Next.js and Supabase.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased selection:bg-black selection:text-white dark:selection:bg-white dark:selection:text-black`}
    >
      <body className="min-h-full flex flex-col">
        <AmbientBackground />
        <Navbar />
        <main className="flex-1 pt-32 pb-12 px-6 max-w-4xl mx-auto w-full">
            {children}
        </main>
      </body>
    </html>
  );
}
