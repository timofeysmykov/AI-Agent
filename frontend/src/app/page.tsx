'use client';

import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';
import { AppBar, Toolbar, Typography, Container, Box, CircularProgress } from '@mui/material';
import ThemeToggle from '@/components/ThemeToggle';
import ChatHistory from '@/components/ChatHistory';
import ChatInput from '@/components/ChatInput';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Загрузка сообщений из localStorage при инициализации
  useEffect(() => {
    const savedMessages = localStorage.getItem('chatMessages');
    if (savedMessages) {
      try {
        setMessages(JSON.parse(savedMessages));
      } catch (e) {
        console.error('Ошибка при загрузке истории чата:', e);
        localStorage.removeItem('chatMessages');
      }
    }
  }, []);

  // Сохранение сообщений в localStorage при изменении
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('chatMessages', JSON.stringify(messages));
    }
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/chat', { message: content });
      
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: response.data.response,
        timestamp: response.data.timestamp || new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Ошибка при отправке сообщения:', err);
      setError('Произошла ошибка при обработке запроса. Пожалуйста, попробуйте еще раз.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    if (window.confirm('Вы уверены, что хотите очистить историю чата?')) {
      setMessages([]);
      localStorage.removeItem('chatMessages');
    }
  };

  const handleSaveHistory = () => {
    try {
      const dataStr = JSON.stringify(messages, null, 2);
      const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
      
      const exportFileDefaultName = `chat-history-${new Date().toISOString().slice(0, 10)}.json`;
      
      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', exportFileDefaultName);
      linkElement.click();
    } catch (err) {
      console.error('Ошибка при сохранении истории:', err);
      setError('Не удалось сохранить историю чата.');
    }
  };

  return (
    <Box className="flex flex-col h-screen bg-background-light dark:bg-background-dark transition-colors duration-300">
      <AppBar position="static" color="transparent" elevation={0} className="border-b border-gray-200 dark:border-gray-700">
        <Toolbar>
          <Typography variant="h6" component="div" className="flex-grow font-bold">
            🦉 AI Assistant
          </Typography>
          <ThemeToggle />
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" className="flex-grow flex flex-col py-4 h-full">
        {error && (
          <div className="bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 p-3 rounded-md mb-4 animate-fade-in">
            {error}
          </div>
        )}

        <Box className="flex-grow overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm transition-all duration-300">
          <ChatHistory
            messages={messages}
            onClearHistory={handleClearHistory}
            onSaveHistory={handleSaveHistory}
            isLoading={isLoading}
          />
        </Box>

        <Box className="mt-4">
          <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        </Box>
      </Container>
    </Box>
  );
} 