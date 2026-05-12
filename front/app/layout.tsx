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
  const siteTitle = siteConfig?.title || "Xiaobaicai Space";
  const footerText =
    siteConfig?.footer?.copyright ||
    siteConfig?.footer?.text ||
    `${siteTitle}. Crafted for writing and systems.`;
  const socialLinks = siteConfig?.social_links || [];
  const footerLinks = siteConfig?.footer?.links || [];
  const icpBeian = siteConfig?.icp_beian;

  return (
    <html
      lang="zh-CN"
      suppressHydrationWarning
      className={`${manrope.variable} ${cormorant.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-canvas text-ink">
        <AmbientBackground />
        <Navbar siteTitle={siteTitle} />
        <main className="flex-1 pt-28 pb-16 px-5 md:px-7 max-w-6xl mx-auto w-full">
          {children}
        </main>
        <footer className="w-full px-5 md:px-7 pb-10">
          <div className="max-w-6xl mx-auto rounded-4xl card-surface px-6 py-6 md:px-8 md:py-7 text-sm text-ink-muted">
            <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
              <div className="min-w-0">
                <p className="text-ink font-medium">{siteTitle}</p>
                <p className="mt-2 leading-relaxed">{footerText}</p>
                {icpBeian ? (
                  <p className="mt-3 text-xs tracking-wide uppercase text-ink-muted/80">备案: {icpBeian}</p>
                ) : null}
              </div>

              <div className="flex flex-col gap-5 md:items-end">
                {socialLinks.length > 0 ? (
                  <div>
                    <p className="text-xs uppercase tracking-[0.14em] text-ink-muted/80">Social</p>
                    <div className="mt-2 flex flex-wrap gap-2 md:justify-end">
                      {socialLinks.map((link) => (
                        <a
                          key={`${link.name}-${link.url}`}
                          href={link.url}
                          target="_blank"
                          rel="noreferrer"
                          className="rounded-full border border-line bg-white/55 px-3 py-1.5 text-xs text-ink-muted hover:text-ink hover:bg-white/80 transition-colors"
                        >
                          {link.name}
                        </a>
                      ))}
                    </div>
                  </div>
                ) : null}

                {footerLinks.length > 0 ? (
                  <div>
                    <p className="text-xs uppercase tracking-[0.14em] text-ink-muted/80 md:text-right">Links</p>
                    <div className="mt-2 flex flex-wrap gap-2 md:justify-end">
                      {footerLinks.map((link) => (
                        <a
                          key={`${link.name}-${link.url}`}
                          href={link.url}
                          target="_blank"
                          rel="noreferrer"
                          className="rounded-full border border-line bg-white/55 px-3 py-1.5 text-xs text-ink-muted hover:text-ink hover:bg-white/80 transition-colors"
                        >
                          {link.name}
                        </a>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
