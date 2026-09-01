import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "100x Resume — Candidate Verification & Resume Intelligence",
  description:
    "AI-powered candidate verification platform. Upload a resume, connect developer profiles, and generate a recruiter-ready evidence-backed Candidate Report.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}