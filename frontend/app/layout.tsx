import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://vyaparsetu.local"),
  title: {
    default: "VyaparSetu | GST, FSSAI and Udyam Registration Support",
    template: "%s | VyaparSetu",
  },
  description:
    "VyaparSetu helps Indian MSMEs prepare GST Registration, FSSAI Registration, and Udyam Registration applications with guided document review.",
  openGraph: {
    title: "VyaparSetu",
    description:
      "GST, FSSAI and Udyam registration support for Indian MSMEs with guided document review.",
    type: "website",
    url: "https://vyaparsetu.local",
    siteName: "VyaparSetu",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
            <Link href="/" className="text-lg font-bold tracking-wide text-ink">
              VyaparSetu
            </Link>
            <nav className="flex items-center gap-3 text-sm font-medium">
              <Link href="/dashboard" className="text-slate-700">
                Dashboard
              </Link>
              <Link href="/auth/login" className="rounded-md bg-ink px-3 py-2 text-white">
                Login
              </Link>
            </nav>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
