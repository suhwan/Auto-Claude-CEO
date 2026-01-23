/**
 * TerminalOutput - Terminal-style output display component
 *
 * Displays CLI output in a terminal-like interface with:
 * - Dark theme styling
 * - Auto-scroll on new output
 * - Running state indicator with animated cursor
 * - Traffic light header decoration
 */

import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

interface TerminalOutputProps {
  output: string;
  isRunning: boolean;
  className?: string;
  title?: string;
}

export function TerminalOutput({ output, isRunning, className, title }: TerminalOutputProps) {
  const { t } = useTranslation(['tasks']);
  const outputRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when output changes
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  return (
    <div className={cn(
      'bg-zinc-900 text-zinc-100 rounded-lg font-mono text-sm h-full flex flex-col overflow-hidden',
      className
    )}>
      {/* Terminal header with traffic lights */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-zinc-700 shrink-0">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <div className="w-3 h-3 rounded-full bg-green-500" />
        </div>
        <span className="text-zinc-400 text-xs">
          {title || t('tasks:gsd.terminal.title', 'GSD Terminal')}
        </span>
        {isRunning && (
          <Loader2 className="h-3 w-3 animate-spin text-primary ml-auto" />
        )}
      </div>

      {/* Output content */}
      <div
        ref={outputRef}
        className="flex-1 overflow-auto p-4 whitespace-pre-wrap break-words"
      >
        {output || (
          <span className="text-zinc-500">
            {t('tasks:gsd.terminal.placeholder', 'Select an action above to start...')}
          </span>
        )}

        {/* Animated cursor when running */}
        {isRunning && (
          <span className="animate-pulse text-primary">|</span>
        )}
      </div>
    </div>
  );
}

export default TerminalOutput;
