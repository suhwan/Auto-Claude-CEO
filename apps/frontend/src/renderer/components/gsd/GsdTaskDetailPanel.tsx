/**
 * GSD Task Detail Panel
 *
 * Slide-out panel showing task details with Plan, Research, and Execute actions.
 * Displays real-time terminal output during execution.
 */

import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { X, Play, Search, FileCode, Loader2, StopCircle, GitBranch, Shield } from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import { Separator } from '../ui/separator';
import { TerminalOutput } from './TerminalOutput';
import type { GsdConvertedTask } from '../../../preload/api/modules/gsd-api';
import { cn } from '../../lib/utils';

// Extended task type with metadata
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

  const [output, setOutput] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentAction, setCurrentAction] = useState<ActionType>(null);

  // Cleanup event listeners on unmount
  useEffect(() => {
    return () => {
      // Cleanup any listeners
      if (window.electronAPI?.gsd) {
        // Listeners are automatically cleaned up when component unmounts
      }
    };
  }, []);

  // Handle Plan action
  const handlePlan = useCallback(async () => {
    if (isRunning) return;

    setIsRunning(true);
    setCurrentAction('plan');
    setOutput([`Starting plan for Phase ${task.phaseNumber}...`]);

    try {
      // Setup event listeners
      const removeOutputListener = window.electronAPI.gsd.onPlanOutput((_event, line) => {
        setOutput(prev => [...prev, line]);
      });

      const removeCompleteListener = window.electronAPI.gsd.onPlanComplete((_event, success) => {
        setOutput(prev => [...prev, success ? '✓ Plan completed successfully' : '✗ Plan failed']);
        setIsRunning(false);
        setCurrentAction(null);
        removeOutputListener();
        removeCompleteListener();

        if (success) {
          onTaskUpdate({ ...task, status: 'in_progress' });
        }
      });

      await window.electronAPI.gsd.planPhase(projectPath, {
        phaseNumber: task.phaseNumber
      });
    } catch (error) {
      setOutput(prev => [...prev, `Error: ${error}`]);
      setIsRunning(false);
      setCurrentAction(null);
    }
  }, [task, projectPath, isRunning, onTaskUpdate]);

  // Handle Research action
  const handleResearch = useCallback(async () => {
    if (isRunning) return;

    setIsRunning(true);
    setCurrentAction('research');
    setOutput([`Starting research for Phase ${task.phaseNumber}...`]);

    try {
      const removeOutputListener = window.electronAPI.gsd.onPlanOutput((_event, line) => {
        setOutput(prev => [...prev, line]);
      });

      const removeCompleteListener = window.electronAPI.gsd.onPlanComplete((_event, success) => {
        setOutput(prev => [...prev, success ? '✓ Research completed successfully' : '✗ Research failed']);
        setIsRunning(false);
        setCurrentAction(null);
        removeOutputListener();
        removeCompleteListener();
      });

      await window.electronAPI.gsd.researchPhase(projectPath, {
        phaseNumber: task.phaseNumber
      });
    } catch (error) {
      setOutput(prev => [...prev, `Error: ${error}`]);
      setIsRunning(false);
      setCurrentAction(null);
    }
  }, [task, projectPath, isRunning]);

  // Handle Execute action
  const handleExecute = useCallback(async () => {
    if (isRunning || !task.planPath) return;

    setIsRunning(true);
    setCurrentAction('execute');
    setOutput([`Executing plan: ${task.planPath}...`]);

    try {
      const removeOutputListener = window.electronAPI.gsd.onExecuteOutput((_event, line) => {
        setOutput(prev => [...prev, line]);
      });

      const removeProgressListener = window.electronAPI.gsd.onExecuteProgress((_event, current, total) => {
        setOutput(prev => [...prev, `Progress: [${current}/${total}]`]);
      });

      const removeCompleteListener = window.electronAPI.gsd.onExecuteComplete((_event, success) => {
        setOutput(prev => [...prev, success ? '✓ Execution completed successfully' : '✗ Execution failed']);
        setIsRunning(false);
        setCurrentAction(null);
        removeOutputListener();
        removeProgressListener();
        removeCompleteListener();

        if (success) {
          onTaskUpdate({ ...task, status: 'complete' });
        }
      });

      await window.electronAPI.gsd.executePlan(projectPath, {
        planPath: task.planPath
      });
    } catch (error) {
      setOutput(prev => [...prev, `Error: ${error}`]);
      setIsRunning(false);
      setCurrentAction(null);
    }
  }, [task, projectPath, isRunning, onTaskUpdate]);

  // Handle Cancel action
  const handleCancel = useCallback(async () => {
    if (!isRunning) return;

    try {
      await window.electronAPI.gsd.cancelPlan(projectPath);
      setOutput(prev => [...prev, '⚠ Operation cancelled by user']);
      setIsRunning(false);
      setCurrentAction(null);
    } catch (error) {
      setOutput(prev => [...prev, `Error cancelling: ${error}`]);
    }
  }, [projectPath, isRunning]);

  // Status badge color
  const statusColor = {
    pending: 'bg-zinc-500',
    in_progress: 'bg-blue-500',
    complete: 'bg-green-500'
  }[task.status];

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-background border-l border-border shadow-xl z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-semibold truncate">{task.title}</h2>
          <p className="text-sm text-muted-foreground">
            Phase {task.phaseNumber}, Plan {task.planNumber}
          </p>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1 p-4">
        {/* Status & Metadata */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge className={cn(statusColor, 'text-white')}>
              {task.status.replace('_', ' ')}
            </Badge>
            {task.parallelSafe && (
              <Badge variant="outline" className="gap-1">
                <Shield className="h-3 w-3" />
                Parallel Safe
              </Badge>
            )}
            {task.dependsOn.length > 0 && (
              <Badge variant="outline" className="gap-1">
                <GitBranch className="h-3 w-3" />
                {task.dependsOn.length} deps
              </Badge>
            )}
          </div>

          {/* Description */}
          <div>
            <h3 className="text-sm font-medium mb-1">Description</h3>
            <p className="text-sm text-muted-foreground">{task.description || 'No description'}</p>
          </div>

          {/* Dependencies */}
          {task.dependsOn.length > 0 && (
            <div>
              <h3 className="text-sm font-medium mb-1">Dependencies</h3>
              <div className="flex flex-wrap gap-1">
                {task.dependsOn.map(dep => (
                  <Badge key={dep} variant="secondary" className="text-xs">
                    {dep}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <Separator />

          {/* Action Buttons */}
          <div className="space-y-2">
            <h3 className="text-sm font-medium">Actions</h3>
            <div className="grid grid-cols-3 gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handlePlan}
                disabled={isRunning}
                className="gap-1"
              >
                {currentAction === 'plan' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileCode className="h-4 w-4" />
                )}
                Plan
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleResearch}
                disabled={isRunning}
                className="gap-1"
              >
                {currentAction === 'research' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
                Research
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExecute}
                disabled={isRunning || !task.planPath}
                className="gap-1"
              >
                {currentAction === 'execute' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                Execute
              </Button>
            </div>

            {isRunning && (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleCancel}
                className="w-full gap-1"
              >
                <StopCircle className="h-4 w-4" />
                Cancel
              </Button>
            )}
          </div>

          <Separator />

          {/* Terminal Output */}
          <div>
            <h3 className="text-sm font-medium mb-2">Output</h3>
            <TerminalOutput
              output={output}
              isRunning={isRunning}
              className="h-48"
            />
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
