import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LogisParse",
  description: "Verificacion documental inteligente para PDFs SII y logisticos chilenos"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
