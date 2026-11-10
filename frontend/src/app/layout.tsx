import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Acadza Faculty Review Console",
  description: "AI Report-to-Fix System for Acadza JEE/NEET Question Bank",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 antialiased">{children}</body>
    </html>
  );
}

