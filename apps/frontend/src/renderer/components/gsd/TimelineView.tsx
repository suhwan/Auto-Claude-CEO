import { CheckCircle2, Circle, PlayCircle } from 'lucide-react';
import { Badge } from '../ui/badge';
import { cn } from '../../lib/utils';
import type { GsdPhaseInfo } from '../../../preload/api/modules/gsd-api';

interface TimelineViewProps {
  phases: GsdPhaseInfo[];
  currentPhase: number;
  onPhaseClick?: (phase: GsdPhaseInfo) => void;
}

export function TimelineView({ phases, currentPhase, onPhaseClick }: TimelineViewProps) {
  const getPhaseIcon = (status: string, isCurrent: boolean) => {
    if (status === 'complete') {
      return <CheckCircle2 className="h-6 w-6 text-green-500" />;
    }
    if (isCurrent || status === 'in_progress') {
      return <PlayCircle className="h-6 w-6 text-blue-500 animate-pulse" />;
    }
    return <Circle className="h-6 w-6 text-gray-400" />;
  };

  const getPhaseColor = (status: string, isCurrent: boolean) => {
    if (status === 'complete') return 'border-green-500 bg-green-50 dark:bg-green-950/30';
    if (isCurrent || status === 'in_progress') return 'border-blue-500 bg-blue-50 dark:bg-blue-950/30';
    return 'border-gray-300 bg-gray-50 dark:bg-gray-900/30 dark:border-gray-700';
  };

  const getLineColor = (fromComplete: boolean) => {
    if (fromComplete) return 'bg-green-500';
    return 'bg-gray-300 dark:bg-gray-700';
  };

  return (
    <div className="overflow-x-auto pb-2">
      <div className="flex items-center gap-1 min-w-max px-2">
        {phases.map((phase, index) => {
          const isCurrent = phase.number === currentPhase;
          const prevComplete = index > 0 && phases[index - 1].status === 'complete';

          return (
            <div key={phase.number} className="flex items-center">
              {/* Connection line */}
              {index > 0 && (
                <div
                  className={cn(
                    'h-0.5 w-6 transition-colors',
                    getLineColor(prevComplete)
                  )}
                />
              )}

              {/* Phase node */}
              <div
                className={cn(
                  'flex flex-col items-center p-2 rounded-lg border-2 cursor-pointer transition-all hover:scale-105',
                  getPhaseColor(phase.status, isCurrent),
                  isCurrent && 'ring-2 ring-blue-400 ring-offset-2 dark:ring-offset-gray-900'
                )}
                onClick={() => onPhaseClick?.(phase)}
              >
                {getPhaseIcon(phase.status, isCurrent)}
                <span className="text-xs font-medium mt-1">P{phase.number}</span>
                <span className="text-[10px] text-muted-foreground max-w-[60px] truncate text-center">
                  {phase.name}
                </span>
                {phase.total_plans > 0 && (
                  <Badge
                    variant={phase.status === 'complete' ? 'default' : 'secondary'}
                    className="text-[10px] mt-1"
                  >
                    {phase.completed_plans}/{phase.total_plans}
                  </Badge>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
