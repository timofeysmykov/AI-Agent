'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { materialDark, materialLight } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { useTheme } from 'next-themes';
import { Avatar, IconButton, Tooltip } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';

interface ChatMessageProps {
  message: {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
  };
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const { theme } = useTheme();
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={`message message-${message.role} animate-fade-in`}>
      <div className="flex items-start gap-3">
        <Avatar className={message.role === 'assistant' ? 'bg-indigo-600' : 'bg-gray-600'}>
          {message.role === 'assistant' ? <SmartToyIcon /> : <PersonIcon />}
        </Avatar>
        <div className="flex-1">
          <div className="flex justify-between items-center mb-1">
            <span className="font-medium">
              {message.role === 'assistant' ? 'AI Ассистент' : 'Вы'}
            </span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">
                {message.timestamp && formatDate(message.timestamp)}
              </span>
              {message.role === 'assistant' && (
                <Tooltip title={copied ? 'Скопировано!' : 'Копировать'}>
                  <IconButton size="small" onClick={copyToClipboard}>
                    {copied ? <CheckIcon fontSize="small" /> : <ContentCopyIcon fontSize="small" />}
                  </IconButton>
                </Tooltip>
              )}
            </div>
          </div>
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <div className="code-block">
                      <div className="code-header">
                        <span>{match[1]}</span>
                        <Tooltip title={copied ? 'Скопировано!' : 'Копировать'}>
                          <IconButton size="small" onClick={() => {
                            navigator.clipboard.writeText(String(children).replace(/\n$/, ''));
                            setCopied(true);
                            setTimeout(() => setCopied(false), 2000);
                          }}>
                            {copied ? <CheckIcon fontSize="small" /> : <ContentCopyIcon fontSize="small" />}
                          </IconButton>
                        </Tooltip>
                      </div>
                      <SyntaxHighlighter
                        style={theme === 'dark' ? materialDark : materialLight}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    </div>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                }
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
} 