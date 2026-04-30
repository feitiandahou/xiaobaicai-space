import { AmbientBackground } from "@/components/layout/AmbientBackground";
import { Navbar } from "@/components/layout/Navbar";
import { fetchSiteConfig } from "@/lib/api";
import type { Metadata } from "next";
import { Cormorant_Garamond, Manrope } from "next/font/google";
import "./globals.css";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
});

const cormorant = Cormorant_Garamond({
  variable: "--font-cormorant",
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
});

export async function generateMetadata(): Promise<Metadata> {
  const siteConfig = await fetchSiteConfig();
  const siteTitle = siteConfig?.title || "Xiaobaicai Space";
  const siteDescription =
    siteConfig?.description ||
    siteConfig?.subtitle ||
    "An editorial-styled personal publication powered by Next.js and FastAPI.";

  return {
    metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
    title: {
      default: siteTitle,
      template: `%s | ${siteTitle}`,
    },
    description: siteDescription,
    openGraph: {
      type: "website",
      siteName: siteTitle,
      title: siteTitle,
      description: siteDescription,
    },
    twitter: {
      card: "summary_large_image",
      title: siteTitle,
      description: siteDescription,
    },
  };
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const siteConfig = await fetchSiteConfig();
  const footerText =
    siteConfig?.footer?.copyright ||
    siteConfig?.footer?.text ||
    `${siteConfig?.title || "Xiaobaicai Space"}. Crafted for writing and systems.`;

  return (
    <html
      lang="zh-CN"
      suppressHydrationWarning
      className={`${manrope.variable} ${cormorant.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-canvas text-ink">
        <AmbientBackground />
        <Navbar />
        <main className="flex-1 pt-28 pb-16 px-5 md:px-7 max-w-6xl mx-auto w-full">
          {children}
        </main>
        <footer className="w-full px-5 md:px-7 pb-10 text-center text-sm text-ink-muted">{footerText}</footer>
      </body>
    </html>
  );
}
