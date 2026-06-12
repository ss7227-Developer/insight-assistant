import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Insights Assistant",
  description: "AI-powered domain-specific document Q&A",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full bg-white text-slate-900 antialiased">{children}</body>
    </html>
  );
}
