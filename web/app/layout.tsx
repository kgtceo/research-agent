import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "research-agent",
  description: "A tool-using agent that researches a company into an interview briefing.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
