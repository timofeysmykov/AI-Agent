'use client';

import './globals.css';
import { Inter } from 'next/font/google';
import { ThemeProvider } from 'next-themes';
import { useState, useEffect } from 'react';

const inter = Inter({ subsets: ['latin', 'cyrillic'] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mounted, setMounted] = useState(false);

  // Предотвращение гидратации
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <html lang="ru">
        <body className={inter.className}>
          <div className="flex items-center justify-center min-h-screen">
            <div className="animate-pulse-slow">Загрузка...</div>
          </div>
        </body>
      </html>
    );
  }

  return (
    <html lang="ru" suppressHydrationWarning>
      <head>
        <title>AI Assistant</title>
        <meta name="description" content="Ваш персональный AI ассистент" />
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
} 