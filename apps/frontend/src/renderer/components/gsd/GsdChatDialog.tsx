/**
 * GsdChatDialog - Chat-based dialog for converting ideas to GSD projects
 *
 * Provides a conversational interface with Claude to gather project requirements
 * and create a GSD project structure with .planning/ directory.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { ScrollArea } from '../ui/scroll-area';
import { Alert, AlertDescription } from '../ui/alert';
import { Loader2, Send, Bot, User, CheckCircle2, X } from 'lucide-react';
import { cn } from '../../../shared/utils/cn';
import type { Idea } from '../../../shared/types';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface GsdChatDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  idea: Idea | null;
  projectPath: string;
  onComplete: (gsdProjectPath: string) => void;
}

export function GsdChatDialog({
  open,
  onOpenChange,
  idea,
  projectPath,
  onComplete
}: GsdChatDialogProps) {
  const { t } = useTranslation(['navigation', 'common']);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [userInput, setUserInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Start chat session when dialog opens
  useEffect(() => {
    if (open && idea && !sessionId && !isStarting) {
      startChatSession();
    }
  }, [open, idea, sessionId, isStarting]);

  // Setup event listeners for chat streaming
  useEffect(() => {
    if (!sessionId) return;

    const unsubMessage = window.electronAPI?.gsd?.onChatMessage?.((chunk: string) => {
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.role === 'assistant' && lastMsg.isStreaming) {
          // Append to existing streaming message
          return [
            ...prev.slice(0, -1),
            { ...lastMsg, content: lastMsg.content + chunk }
          ];
        } else {
          // Start new streaming message
          return [
            ...prev,
            {
              id: `msg-${Date.now()}`,
              role: 'assistant',
              content: chunk,
              timestamp: new Date(),
              isStreaming: true
            }
          ];
        }
      });
    });

    const unsubComplete = window.electronAPI?.gsd?.onChatComplete?.((result: { gsdPath: string }) => {
      setIsStreaming(false);
      setIsComplete(true);
      // Mark last message as not streaming
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.isStreaming) {
          return [...prev.slice(0, -1), { ...lastMsg, isStreaming: false }];
        }
        return prev;
      });
      // Notify parent of completion
      onComplete(result.gsdPath);
    });

    const unsubError = window.electronAPI?.gsd?.onChatError?.((errorMsg: string) => {
      setIsStreaming(false);
      setError(errorMsg);
      // Mark last message as not streaming
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.isStreaming) {
          return [...prev.slice(0, -1), { ...lastMsg, isStreaming: false }];
        }
        return prev;
      });
    });

    return () => {
      unsubMessage?.();
      unsubComplete?.();
      unsubError?.();
    };
  }, [sessionId, onComplete]);

  // Focus input when not streaming
  useEffect(() => {
    if (!isStreaming && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isStreaming]);

  const startChatSession = useCallback(async () => {
    if (!idea) return;

    setIsStarting(true);
    setMessages([]);
    setError(null);
    setIsComplete(false);

    try {
      const result = await window.electronAPI?.gsd?.startChatSession?.(projectPath, {
        title: idea.title,
        description: idea.description,
        rationale: idea.rationale
      });

      if (result?.success && result.data?.sessionId) {
        setSessionId(result.data.sessionId);
        setIsStreaming(true);
      } else {
        setError(result?.error || t('navigation:gsd.chatDialog.error'));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t('navigation:gsd.chatDialog.error'));
    } finally {
      setIsStarting(false);
    }
  }, [idea, projectPath, t]);

  const handleSend = useCallback(async () => {
    if (!userInput.trim() || !sessionId || isStreaming) return;

    const message = userInput.trim();
    setUserInput('');

    // Add user message to chat
    setMessages(prev => [
      ...prev,
      {
        id: `msg-${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date()
      }
    ]);

    setIsStreaming(true);
    setError(null);

    try {
      await window.electronAPI?.gsd?.sendChatMessage?.(sessionId, message);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('navigation:gsd.chatDialog.error'));
      setIsStreaming(false);
    }
  }, [userInput, sessionId, isStreaming, t]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const handleClose = useCallback(async () => {
    // End session if active
    if (sessionId) {
      try {
        await window.electronAPI?.gsd?.endChatSession?.(sessionId);
      } catch {
        // Ignore errors on cleanup
      }
    }

    // Reset state
    setSessionId(null);
    setMessages([]);
    setUserInput('');
    setIsStreaming(false);
    setError(null);
    setIsComplete(false);
    setIsStarting(false);

    onOpenChange(false);
  }, [sessionId, onOpenChange]);

  if (!idea) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl h-[600px] flex flex-col p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b">
          <DialogTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            {t('navigation:gsd.chatDialog.title', { title: idea.title })}
          </DialogTitle>
          <DialogDescription>
            {t('navigation:gsd.chatDialog.description')}
          </DialogDescription>
        </DialogHeader>

        {/* Chat messages area */}
        <ScrollArea className="flex-1 px-6">
          <div className="space-y-4 py-4">
            {isStarting && (
              <div className="flex items-center justify-center gap-2 text-muted-foreground py-8">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>{t('navigation:gsd.chatDialog.starting')}</span>
              </div>
            )}

            {messages.map((msg) => (
              <ChatBubble key={msg.id} message={msg} />
            ))}

            {isStreaming && messages[messages.length - 1]?.role !== 'assistant' && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>{t('navigation:gsd.chatDialog.thinking')}</span>
              </div>
            )}

            {isComplete && (
              <div className="flex items-center gap-2 text-green-600 bg-green-50 dark:bg-green-950/20 p-3 rounded-lg">
                <CheckCircle2 className="h-5 w-5" />
                <span>{t('navigation:gsd.chatDialog.conversationComplete')}</span>
              </div>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input area */}
        <div className="border-t p-4">
          {!isComplete ? (
            <div className="flex gap-2">
              <Input
                ref={inputRef}
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={t('navigation:gsd.chatDialog.inputPlaceholder')}
                disabled={isStreaming || isStarting}
                className="flex-1"
              />
              <Button
                onClick={handleSend}
                disabled={isStreaming || isStarting || !userInput.trim()}
                size="icon"
              >
                {isStreaming ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          ) : (
            <div className="flex justify-end">
              <Button onClick={handleClose}>
                {t('navigation:gsd.chatDialog.close')}
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * ChatBubble - Renders a single chat message
 */
function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  return (
    <div
      className={cn(
        'flex gap-3',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div
        className={cn(
          'max-w-[80%] rounded-lg px-4 py-2',
          isUser
            ? 'bg-primary text-primary-foreground'
            : isSystem
            ? 'bg-muted/50 text-muted-foreground italic'
            : 'bg-muted'
        )}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        {message.isStreaming && (
          <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
        )}
      </div>
    </div>
  );
}
