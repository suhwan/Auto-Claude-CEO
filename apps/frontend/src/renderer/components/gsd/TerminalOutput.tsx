import { useEffect, useRef } from 'react';
import { cn } from '../../lib/utils';

interface TerminalOutputProps {
  output: string[];
  isRunning?: boolean;
  className?: string;
}

export function TerminalOutput({ output, isRunning = false, className }: TerminalOutputProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new output arrives
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [output]);

  return (
    <div className={cn("rounded-lg overflow-hidden border border-border", className)}>
      {/* Traffic light header */}
      <div className="flex items-center gap-1.5 px-3 py-2 bg-zinc-800 border-b border-zinc-700">
        <div className="w-3 h-3 rounded-full bg-red-500" />
        <div className="w-3 h-3 rounded-full bg-yellow-500" />
        <div className="w-3 h-3 rounded-full bg-green-500" />
        <span className="ml-2 text-xs text-zinc-400">Terminal</span>
      </div>

      {/* Terminal content */}
      <div
        ref={scrollRef}
        className="bg-zinc-900 p-4 font-mono text-sm text-zinc-100 h-64 overflow-y-auto"
      >
        {output.length === 0 ? (
          <span className="text-zinc-500">Waiting for output...</span>
        ) : (
          output.map((line, index) => (
            <div key={index} className="whitespace-pre-wrap">
              {colorizeOutput(line)}
            </div>
          ))
        )}

        {/* Animated cursor */}
        {isRunning && (
          <span className="inline-block w-2 h-4 bg-zinc-100 animate-pulse ml-1" />
        )}
      </div>
    </div>
  );
}

// Colorize terminal output based on content
function colorizeOutput(line: string): React.ReactNode {
  // Success indicators (green)
  if (line.includes('✓') || line.includes('✅') || line.includes('success') || line.includes('complete')) {
    return <span className="text-green-400">{line}</span>;
  }

  // Error indicators (red)
  if (line.includes('✗') || line.includes('❌') || line.includes('error') || line.includes('failed')) {
    return <span className="text-red-400">{line}</span>;
  }

  // Action indicators (blue)
  if (line.includes('🔧') || line.includes('📁') || line.includes('→') || line.startsWith('[')) {
    return <span className="text-blue-400">{line}</span>;
  }

  // Warning indicators (yellow)
  if (line.includes('⚠') || line.includes('warning') || line.includes('warn')) {
    return <span className="text-yellow-400">{line}</span>;
  }

  return line;
}
