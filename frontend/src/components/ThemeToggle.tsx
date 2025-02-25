'use client';

import { useTheme } from 'next-themes';
import { useState, useEffect } from 'react';
import { IconButton } from '@mui/material';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Предотвращение гидратации
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return (
    <IconButton
      onClick={toggleTheme}
      color="inherit"
      aria-label="toggle theme"
      className="transition-all duration-300"
    >
      {theme === 'dark' ? (
        <Brightness7Icon className="text-yellow-300" />
      ) : (
        <Brightness4Icon className="text-indigo-600" />
      )}
    </IconButton>
  );
} 