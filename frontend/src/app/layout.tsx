import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ApplyTrack — your search, in motion",
  description: "A calmer, more organized way to manage your job search.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
