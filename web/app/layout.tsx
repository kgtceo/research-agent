import type { Metadata } from "next";
import "./globals.css";

const url = "https://agent.kareemghazal.com";
const title = "research-agent — a tool-using company research agent";
const description =
  "An agent that plans, searches the web, reads pages, and writes a sourced brief — with guardrails and source-grounding evals that catch fabricated citations. Live + open-source.";

export const metadata: Metadata = {
  metadataBase: new URL(url),
  title,
  description,
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    url,
    siteName: "research-agent",
    title,
    description,
    locale: "en_GB",
    images: [
      {
        url: "/og.jpg",
        width: 1200,
        height: 630,
        alt: "research-agent — a tool-using research agent with source-grounding evals",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title,
    description,
    images: ["/og.jpg"],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
