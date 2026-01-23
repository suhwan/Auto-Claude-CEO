/**
 * TerminalOutput - CLI-style terminal output display
 */

import { useRef, useEffect } from 'react';
import { cn } from '../../lib/utils';

interface TerminalOutputProps {
  output: string;
  isRunning?: boolean;
  className?: string;
}

export function TerminalOutput({ output, isRunning = false, className }: TerminalOutputProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new output
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [output]);

  return (
    <div className={cn('rounded-lg overflow-hidden', className)}>
      {/* Traffic light header */}
      <div className="bg-gray-800 px-3 py-2 flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-red-500" />
        <div className="w-3 h-3 rounded-full bg-yellow-500" />
        <div className="w-3 h-3 rounded-full bg-green-500" />
        <span className="ml-2 text-gray-400 text-xs">Terminal</span>
      </div>

      {/* Terminal content */}
      <div
        ref={scrollRef}
        className="bg-gray-900 p-4 font-mono text-sm text-gray-100 h-64 overflow-auto"
      >
        {output ? (
          <pre className="whitespace-pre-wrap">{output}</pre>
        ) : (
          <span className="text-gray-500 italic">Waiting for output...</span>
        )}
        {isRunning && (
          <span className="inline-block w-2 h-4 bg-green-400 animate-pulse ml-1" />
        )}
      </div>
    </div>
  );
}
