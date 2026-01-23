/**
 * ParallelExecutionDashboard - Phase-wide parallel execution UI
 *
 * Displays execution waves, running tasks in a grid,
 * and real-time progress for parallel plan execution.
 */

import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { ScrollArea } from '../ui/scroll-area';
import {
  Play, Square, Zap, CheckCircle2, Circle, AlertCircle,
  Loader2, Clock, XCircle
} from 'lucide-react';
import { TerminalOutput } from './TerminalOutput';
import { cn } from '../../lib/utils';

// Types matching the backend
interface ExecutionWave {
  waveNumber: number;
  tasks: string[];
  isParallel: boolean;
}

interface ExecutionPhase {
  phaseNumber: number;
  phaseName: string;
  waves: ExecutionWave[];
  totalTasks: number;
  parallelizable: number;
}

interface TaskProgress {
  taskId: string;
  planId: string;
  sessionId: string;
  status: 'pending' | 'ready' | 'running' | 'complete' | 'error';
  progress?: number;
  output?: string;
  error?: string;
}

interface PhaseExecutionResult {
  phaseNumber: number;
  totalTasks: number;
  successful: number;
  failed: number;
  duration: number;
}

interface ParallelExecutionDashboardProps {
  projectPath: string;
  phaseNumber: number;
  phaseName?: string;
  onClose: () => void;
}

export function ParallelExecutionDashboard({
  projectPath,
  phaseNumber,
  phaseName,
  onClose
}: ParallelExecutionDashboardProps) {
  const { t } = useTranslation(['tasks', 'common', 'navigation']);
  const [executionPlan, setExecutionPlan] = useState<ExecutionPhase | null>(null);
  const [taskProgress, setTaskProgress] = useState<Map<string, TaskProgress>>(new Map());
  const [isRunning, setIsRunning] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [result, setResult] = useState<PhaseExecutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load execution plan
  useEffect(() => {
    setIsLoading(true);
    setError(null);

    window.electronAPI.gsd.getExecutionPlan(projectPath, phaseNumber)
      .then((plan: ExecutionPhase | null) => {
        setExecutionPlan(plan);
        // Initialize task progress
        if (plan) {
          const initialProgress = new Map<string, TaskProgress>();
          plan.waves.forEach(wave => {
            wave.tasks.forEach(taskId => {
              initialProgress.set(taskId, {
                taskId,
                planId: taskId.replace('gsd-', ''),
                sessionId: '',
                status: 'pending'
              });
            });
          });
          setTaskProgress(initialProgress);
        }
      })
      .catch((err: Error) => {
        setError(err.message);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [projectPath, phaseNumber]);

  // Listen for progress updates
  useEffect(() => {
    const unsubscribe = window.electronAPI.gsd.onParallelProgress((updates: TaskProgress[]) => {
      setTaskProgress(prev => {
        const next = new Map(prev);
        updates.forEach(u => next.set(u.taskId, u));
        return next;
      });
    });

    return () => unsubscribe();
  }, []);

  // Listen for completion
  useEffect(() => {
    const unsubscribe = window.electronAPI.gsd.onParallelComplete((res: PhaseExecutionResult) => {
      setResult(res);
      setIsRunning(false);
    });

    return () => unsubscribe();
  }, []);

  const handleStartAll = useCallback(async () => {
    setIsRunning(true);
    setResult(null);
    setError(null);

    try {
      await window.electronAPI.gsd.executePhaseParallel(projectPath, phaseNumber);
    } catch (err) {
      setError((err as Error).message);
      setIsRunning(false);
    }
  }, [projectPath, phaseNumber]);

  const handleCancel = useCallback(() => {
    window.electronAPI.gsd.cancelParallelExecution();
    setIsRunning(false);
  }, []);

  const runningTasks = Array.from(taskProgress.values())
    .filter(t => t.status === 'running');

  const completedCount = Array.from(taskProgress.values())
    .filter(t => t.status === 'complete').length;

  const failedCount = Array.from(taskProgress.values())
    .filter(t => t.status === 'error').length;

  const totalCount = executionPlan?.totalTasks || 0;
  const overallProgress = totalCount > 0
    ? Math.round((completedCount / totalCount) * 100)
    : 0;

  return (
    <Dialog open onOpenChange={(open) => !open && !isRunning && onClose()}>
      <DialogContent className="max-w-5xl h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            {t('navigation:gsd.parallelExecution', 'Parallel Execution')} - Phase {phaseNumber}
          </DialogTitle>
          <DialogDescription>
            {phaseName || executionPlan?.phaseName}
            {executionPlan && (
              <span className="ml-2">
                ({executionPlan.parallelizable}/{executionPlan.totalTasks} {t('navigation:gsd.canParallel', 'can run in parallel')})
              </span>
            )}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="flex-1 flex flex-col items-center justify-center p-4">
            <AlertCircle className="h-12 w-12 text-destructive mb-4" />
            <p className="text-sm text-destructive">{error}</p>
          </div>
        ) : (
          <>
            {/* Progress bar */}
            {(isRunning || result) && (
              <div className="space-y-2 py-2">
                <div className="flex items-center justify-between text-sm">
                  <span>
                    {completedCount}/{totalCount} {t('common:labels.completed', 'completed')}
                    {failedCount > 0 && (
                      <span className="text-destructive ml-2">
                        ({failedCount} {t('common:labels.failed', 'failed')})
                      </span>
                    )}
                  </span>
                  <span>{overallProgress}%</span>
                </div>
                <Progress value={overallProgress} className="h-2" />
              </div>
            )}

            {/* Wave list */}
            <ScrollArea className="flex-1">
              <div className="space-y-4 py-4 pr-4">
                {executionPlan?.waves.map((wave) => (
                  <div key={wave.waveNumber} className="border rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-medium">
                        Wave {wave.waveNumber}
                      </span>
                      {wave.isParallel && wave.tasks.length > 1 && (
                        <Badge variant="outline" className="text-xs">
                          <Zap className="h-3 w-3 mr-1" />
                          {wave.tasks.length} parallel
                        </Badge>
                      )}
                    </div>

                    <div className={cn(
                      "grid gap-2",
                      wave.tasks.length === 1 && "grid-cols-1",
                      wave.tasks.length === 2 && "grid-cols-2",
                      wave.tasks.length >= 3 && "grid-cols-3"
                    )}>
                      {wave.tasks.map(taskId => {
                        const progress = taskProgress.get(taskId);
                        return (
                          <TaskProgressCard
                            key={taskId}
                            taskId={taskId}
                            progress={progress}
                          />
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>

            {/* Running tasks terminal grid */}
            {runningTasks.length > 0 && (
              <div className="border-t pt-4">
                <div className="text-sm font-medium mb-2 flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {t('navigation:gsd.running', 'Running')} ({runningTasks.length} {t('navigation:gsd.parallel', 'parallel')})
                </div>
                <div className={cn(
                  "grid gap-2 h-[200px]",
                  runningTasks.length === 1 && "grid-cols-1",
                  runningTasks.length === 2 && "grid-cols-2",
                  runningTasks.length >= 3 && "grid-cols-3"
                )}>
                  {runningTasks.map(task => (
                    <div key={task.taskId} className="border rounded-lg overflow-hidden flex flex-col">
                      <div className="bg-muted px-2 py-1 flex items-center justify-between shrink-0">
                        <span className="text-xs font-medium">{task.planId}</span>
                        {task.progress !== undefined && (
                          <span className="text-xs text-muted-foreground">{task.progress}%</span>
                        )}
                      </div>
                      <Progress value={task.progress || 0} className="h-1 rounded-none" />
                      <TerminalOutput
                        output={task.output || ''}
                        isRunning={task.status === 'running'}
                        className="flex-1 min-h-0"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Result summary */}
            {result && (
              <div className={cn(
                "border rounded-lg p-4 mt-4",
                result.failed > 0 ? "border-destructive bg-destructive/10" : "border-green-500 bg-green-50 dark:bg-green-950"
              )}>
                <div className="flex items-center gap-2">
                  {result.failed > 0 ? (
                    <XCircle className="h-5 w-5 text-destructive" />
                  ) : (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  )}
                  <span className="font-medium">
                    {result.failed > 0
                      ? t('navigation:gsd.executionFailed', 'Execution completed with errors')
                      : t('navigation:gsd.executionComplete', 'Execution completed successfully')
                    }
                  </span>
                </div>
                <div className="mt-2 text-sm text-muted-foreground flex items-center gap-4">
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    {result.successful} {t('common:labels.successful', 'successful')}
                  </span>
                  {result.failed > 0 && (
                    <span className="flex items-center gap-1">
                      <XCircle className="h-4 w-4 text-destructive" />
                      {result.failed} {t('common:labels.failed', 'failed')}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {formatDuration(result.duration)}
                  </span>
                </div>
              </div>
            )}
          </>
        )}

        {/* Action buttons */}
        <div className="flex justify-end gap-2 pt-4 border-t">
          {!isRunning ? (
            <>
              <Button variant="outline" onClick={onClose}>
                {t('common:buttons.close', 'Close')}
              </Button>
              {!result && (
                <Button onClick={handleStartAll} disabled={isLoading || !executionPlan}>
                  <Play className="h-4 w-4 mr-1" />
                  {t('navigation:gsd.executeAll', 'Execute All')}
                </Button>
              )}
            </>
          ) : (
            <Button variant="destructive" onClick={handleCancel}>
              <Square className="h-4 w-4 mr-1" />
              {t('common:buttons.cancel', 'Cancel')}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Task progress card component
interface TaskProgressCardProps {
  taskId: string;
  progress?: TaskProgress;
}

function TaskProgressCard({ taskId, progress }: TaskProgressCardProps) {
  const planId = taskId.replace('gsd-', '');
  const status = progress?.status || 'pending';

  const statusIcon = {
    pending: <Circle className="h-4 w-4 text-muted-foreground" />,
    ready: <Circle className="h-4 w-4 text-blue-500" />,
    running: <Loader2 className="h-4 w-4 animate-spin text-primary" />,
    complete: <CheckCircle2 className="h-4 w-4 text-green-500" />,
    error: <AlertCircle className="h-4 w-4 text-destructive" />
  };

  return (
    <div className={cn(
      "border rounded-md p-2 flex items-center gap-2",
      status === 'running' && "border-primary bg-primary/5",
      status === 'complete' && "border-green-500 bg-green-50 dark:bg-green-950",
      status === 'error' && "border-destructive bg-destructive/5"
    )}>
      {statusIcon[status]}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">{planId}</div>
        {status === 'running' && progress?.progress !== undefined && (
          <Progress value={progress.progress} className="h-1 mt-1" />
        )}
        {status === 'error' && progress?.error && (
          <div className="text-xs text-destructive truncate mt-1">{progress.error}</div>
        )}
      </div>
    </div>
  );
}

// Format duration in human readable format
function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`;
  }
  return `${seconds}s`;
}

export default ParallelExecutionDashboard;
