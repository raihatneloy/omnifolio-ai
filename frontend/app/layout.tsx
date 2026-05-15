import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Omnifolio AI",
  description: "Privacy-first portfolio aggregator with AI ingestion",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, -apple-system, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}