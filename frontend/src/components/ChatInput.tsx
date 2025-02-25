'use client';

import { useState, useRef, useEffect } from 'react';
import { IconButton, TextField, Paper } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MicIcon from '@mui/icons-material/Mic';
import StopIcon from '@mui/icons-material/Stop';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export default function ChatInput({ onSendMessage, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Фокус на поле ввода при загрузке
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  const toggleRecording = () => {
    // Здесь будет логика для записи голоса
    setIsRecording(!isRecording);
  };

  return (
    <Paper 
      elevation={3} 
      className="p-2 sticky bottom-4 mx-auto max-w-4xl rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 transition-all duration-300"
    >
      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <IconButton
          color="primary"
          onClick={toggleRecording}
          disabled={isLoading}
          className="transition-all duration-300"
        >
          {isRecording ? <StopIcon /> : <MicIcon />}
        </IconButton>
        
        <TextField
          fullWidth
          placeholder="Напишите сообщение..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          multiline
          maxRows={4}
          disabled={isLoading}
          inputRef={inputRef}
          variant="outlined"
          className="rounded-xl"
          InputProps={{
            className: "rounded-xl bg-gray-50 dark:bg-gray-700 transition-all duration-300",
          }}
        />
        
        <IconButton
          color="primary"
          type="submit"
          disabled={!message.trim() || isLoading}
          className={`transition-all duration-300 ${
            message.trim() && !isLoading ? 'opacity-100' : 'opacity-50'
          }`}
        >
          <SendIcon />
        </IconButton>
      </form>
    </Paper>
  );
} 