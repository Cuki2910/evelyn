import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Evelyn | Content moderation",
  description: "A human-in-the-loop Vietnamese news moderation MVP.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
