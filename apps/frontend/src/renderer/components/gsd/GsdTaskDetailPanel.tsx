/**
 * GsdTaskDetailPanel - Task detail slide-out panel
 *
 * Shows task metadata and provides Plan/Research/Execute actions
 * with real-time terminal output.
 */

import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { X, FileText, Search, Play, Square, ExternalLink } from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import { Separator } from '../ui/separator';
import { TerminalOutput } from './TerminalOutput';
import type { GsdConvertedTask } from '../../../preload/api/modules/gsd-api';

// Extended task type with plan/summary paths
export interface GsdTaskWithMeta extends GsdConvertedTask {
  planPath?: string;
  summaryPath?: string;
}

interface GsdTaskDetailPanelProps {
  task: GsdTaskWithMeta;
  projectPath: string;
  onClose: () => void;
  onTaskUpdate: (task: GsdTaskWithMeta) => void;
}

type ActionType = 'plan' | 'research' | 'execute' | null;

export function GsdTaskDetailPanel({
  task,
  projectPath,
  onClose,
  onTaskUpdate
}: GsdTaskDetailPanelProps) {
  const { t } = useTranslation(['tasks', 'common']);
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [currentAction, setCurrentAction] = useState<ActionType>(null);

  // Clean up event listeners on unmount
  useEffect(() => {
    const handleOutput = (_event: unknown, data: { output: string }) => {
      setOutput(prev => prev + data.output);
    };

    const handleComplete = () => {
      setIsRunning(false);
      setCurrentAction(null);
    };

    const handleError = (_event: unknown, data: { error: string }) => {
      setOutput(prev => prev + `\nError: ${data.error}`);
      setIsRunning(false);
      setCurrentAction(null);
    };

    // Subscribe to events
    window.electronAPI?.gsd?.onPlanOutput?.(handleOutput);
    window.electronAPI?.gsd?.onExecuteOutput?.(handleOutput);
    window.electronAPI?.gsd?.onPlanComplete?.(handleComplete);
    window.electronAPI?.gsd?.onExecuteComplete?.(handleComplete);
    window.electronAPI?.gsd?.onPlanError?.(handleError);
    window.electronAPI?.gsd?.onExecuteError?.(handleError);

    return () => {
      // Cleanup listeners would go here if the API supports it
    };
  }, []);

  const handlePlan = useCallback(async () => {
    if (isRunning) return;
    setIsRunning(true);
    setCurrentAction('plan');
    setOutput(`Planning phase ${task.phaseNumber}...\n\n`);

    try {
      await window.electronAPI?.gsd?.planPhase?.(projectPath, task.phaseNumber, task.phaseName);
    } catch (error) {
      setOutput(prev => prev + `\nFailed to start planning: ${error}`);
      setIsRunning(false);
      setCurrentAction(null);
    }
  }, [isRunning, projectPath, task.phaseNumber, task.phaseName]);

  const handleResearch = useCallback(async () => {
    if (isRunning) return;
    setIsRunning(true);
    setCurrentAction('research');
    setOutput(`Researching phase ${task.phaseNumber}...\n\n`);

    try {
      await window.electronAPI?.gsd?.researchPhase?.(projectPath, task.phaseNumber);
    } catch (error) {
      setOutput(prev => prev + `\nFailed to start research: ${error}`);
      setIsRunning(false);
      setCurrentAction(null);
    }
  }, [isRunning, projectPath, task.phaseNumber]);

  const handleExecute = useCallback(async () => {
    if (isRunning || !task.planPath) return;
    setIsRunning(true);
    setCurrentAction('execute');
    setOutput(`Executing plan: ${task.planPath}...\n\n`);

    try {
      await window.electronAPI?.gsd?.executePlan?.(projectPath, task.planPath, task.title);
    } catch (error) {
      setOutput(prev => prev + `\nFailed to start execution: ${error}`);
      setIsRunning(false);
      setCurrentAction(null);
    }
  }, [isRunning, projectPath, task.planPath, task.title]);

  const handleCancel = useCallback(async () => {
    try {
      await window.electronAPI?.gsd?.cancelPlan?.();
      setOutput(prev => prev + '\n\nCancelled by user.');
      setIsRunning(false);
      setCurrentAction(null);
    } catch (error) {
      console.error('Failed to cancel:', error);
    }
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete': return 'bg-green-500';
      case 'in_progress': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 w-[500px] bg-background border-l shadow-xl z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${getStatusColor(task.status)}`} />
          <h2 className="font-semibold truncate max-w-[350px]">{task.title}</h2>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {/* Task Info */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="outline">Phase {task.phaseNumber}</Badge>
              <Badge variant={task.status === 'complete' ? 'default' : 'secondary'}>
                {task.status}
              </Badge>
              {task.parallel_safe && (
                <Badge variant="outline" className="text-green-600">
                  Parallel Safe
                </Badge>
              )}
            </div>

            {task.depends_on && task.depends_on.length > 0 && (
              <div className="text-sm text-muted-foreground">
                Depends on: {task.depends_on.join(', ')}
              </div>
            )}
          </div>

          <Separator />

          {/* Description */}
          {task.objective && (
            <div>
              <h3 className="text-sm font-medium mb-2">Objective</h3>
              <p className="text-sm text-muted-foreground">{task.objective}</p>
            </div>
          )}

          <Separator />

          {/* Action Buttons */}
          <div className="space-y-2">
            <h3 className="text-sm font-medium">Actions</h3>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handlePlan}
                disabled={isRunning || task.status === 'complete'}
              >
                <FileText className="h-4 w-4 mr-1" />
                Plan
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleResearch}
                disabled={isRunning}
              >
                <Search className="h-4 w-4 mr-1" />
                Research
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={handleExecute}
                disabled={isRunning || !task.planPath}
              >
                <Play className="h-4 w-4 mr-1" />
                Execute
              </Button>
              {isRunning && (
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleCancel}
                >
                  <Square className="h-4 w-4 mr-1" />
                  Cancel
                </Button>
              )}
            </div>
          </div>

          <Separator />

          {/* Terminal Output */}
          <div>
            <h3 className="text-sm font-medium mb-2">
              Output {currentAction && `(${currentAction})`}
            </h3>
            <TerminalOutput output={output} isRunning={isRunning} />
          </div>

          {/* File Links */}
          {(task.planPath || task.summaryPath) && (
            <>
              <Separator />
              <div className="space-y-2">
                <h3 className="text-sm font-medium">Files</h3>
                {task.planPath && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <FileText className="h-4 w-4" />
                    <span>Plan: {task.planPath}</span>
                  </div>
                )}
                {task.summaryPath && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <FileText className="h-4 w-4" />
                    <span>Summary: {task.summaryPath}</span>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
