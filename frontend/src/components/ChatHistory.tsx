'use client';

import { useRef, useEffect } from 'react';
import { Button, Divider } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import SaveIcon from '@mui/icons-material/Save';
import ChatMessage from './ChatMessage';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ChatHistoryProps {
  messages: Message[];
  onClearHistory: () => void;
  onSaveHistory: () => void;
  isLoading: boolean;
}

export default function ChatHistory({
  messages,
  onClearHistory,
  onSaveHistory,
  isLoading,
}: ChatHistoryProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Автоскролл к последнему сообщению
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-semibold">История чата</h2>
        <div className="flex gap-2">
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={onClearHistory}
            size="small"
            disabled={messages.length <= 1}
          >
            Очистить
          </Button>
          <Button
            variant="outlined"
            color="primary"
            startIcon={<SaveIcon />}
            onClick={onSaveHistory}
            size="small"
            disabled={messages.length <= 1}
          >
            Сохранить
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-500 dark:text-gray-400">
              Начните диалог, отправив сообщение
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))
        )}
        
        {isLoading && (
          <div className="typing-indicator">
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
} 