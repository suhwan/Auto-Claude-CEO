/**
 * GsdTaskDetailPanel - Slide-out panel for GSD Task details
 *
 * Displays task information and provides Plan/Research/Execute actions.
 * Shows real-time terminal output during execution.
 */

import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { X, FileText, Search, Play, Check, Zap, Link as LinkIcon, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { TerminalOutput } from './TerminalOutput';
import { cn } from '../../lib/utils';
import type { GsdConvertedTask } from '../../../preload/api/modules/gsd-api';

// Extended task type with additional metadata for execution
export interface GsdTaskWithMeta extends GsdConvertedTask {
  planPath?: string;       // PLAN.md path (if exists, Execute is enabled)
  summaryPath?: string;    // SUMMARY.md path (if exists, task is complete)
}

interface GsdTaskDetailPanelProps {
  task: GsdTaskWithMeta | null;
  projectPath: string;
  onClose: () => void;
  onTaskUpdate?: (task: GsdTaskWithMeta) => void;
}

type ExecutionType = 'plan' | 'research' | 'execute' | null;

export function GsdTaskDetailPanel({
  task,
  projectPath,
  onClose,
  onTaskUpdate
}: GsdTaskDetailPanelProps) {
  const { t } = useTranslation(['tasks', 'common', 'navigation']);

  // Execution state
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionType, setExecutionType] = useState<ExecutionType>(null);
  const [terminalOutput, setTerminalOutput] = useState('');
  const [generatorId, setGeneratorId] = useState<string | null>(null);

  // Reset state when task changes
  useEffect(() => {
    setTerminalOutput('');
    setIsExecuting(false);
    setExecutionType(null);
    setGeneratorId(null);
  }, [task?.id]);

  // Setup event listeners for plan/research/execute output
  useEffect(() => {
    if (!window.electronAPI?.gsd) return;

    // Plan event listeners
    const cleanupPlanOutput = window.electronAPI.gsd.onPlanOutput((data) => {
      if (data.generatorId === generatorId) {
        setTerminalOutput(prev => prev + data.data);
      }
    });

    const cleanupPlanComplete = window.electronAPI.gsd.onPlanComplete((data) => {
      if (data.generatorId === generatorId) {
        setIsExecuting(false);
        if (data.success && task) {
          // Update task to reflect plan created
          onTaskUpdate?.({
            ...task,
            planPath: `.planning/phases/${String(task.phaseNumber).padStart(2, '0')}-*/${task.id.replace('gsd-', '')}-PLAN.md`
          });
        }
      }
    });

    const cleanupPlanError = window.electronAPI.gsd.onPlanError((data) => {
      if (data.generatorId === generatorId) {
        setTerminalOutput(prev => prev + `\n[ERROR] ${data.error}`);
      }
    });

    // Research event listeners
    const cleanupResearchOutput = window.electronAPI.gsd.onResearchOutput((data) => {
      if (data.generatorId === generatorId) {
        setTerminalOutput(prev => prev + data.data);
      }
    });

    const cleanupResearchComplete = window.electronAPI.gsd.onResearchComplete((data) => {
      if (data.generatorId === generatorId) {
        setIsExecuting(false);
      }
    });

    const cleanupResearchError = window.electronAPI.gsd.onResearchError((data) => {
      if (data.generatorId === generatorId) {
        setTerminalOutput(prev => prev + `\n[ERROR] ${data.error}`);
      }
    });

    // Execute event listeners
    const cleanupExecuteOutput = window.electronAPI.gsd.onExecuteOutput((data) => {
      if (data.generatorId === generatorId) {
        setTerminalOutput(prev => prev + data.data);
      }
    });

    const cleanupExecuteComplete = window.electronAPI.gsd.onExecuteComplete((data) => {
      if (data.generatorId === generatorId) {
        setIsExecuting(false);
        if (data.success && task) {
          // Update task to reflect execution complete
          onTaskUpdate?.({
            ...task,
            status: 'complete',
            summaryPath: task.planPath?.replace('-PLAN.md', '-SUMMARY.md')
          });
        }
      }
    });

    const cleanupExecuteError = window.electronAPI.gsd.onExecuteError((data) => {
      if (data.generatorId === generatorId) {
        setTerminalOutput(prev => prev + `\n[ERROR] ${data.error}`);
      }
    });

    return () => {
      cleanupPlanOutput();
      cleanupPlanComplete();
      cleanupPlanError();
      cleanupResearchOutput();
      cleanupResearchComplete();
      cleanupResearchError();
      cleanupExecuteOutput();
      cleanupExecuteComplete();
      cleanupExecuteError();
    };
  }, [generatorId, task, onTaskUpdate]);

  // Handle Plan button click
  const handlePlan = useCallback(async () => {
    if (!task || !window.electronAPI?.gsd) return;

    setIsExecuting(true);
    setExecutionType('plan');
    setTerminalOutput(`$ /gsd:plan-phase ${task.phaseNumber}\n\n`);

    try {
      const result = await window.electronAPI.gsd.planPhase(projectPath, {
        phaseNumber: task.phaseNumber
      });

      if (result.success && result.data) {
        setGeneratorId(result.data.generatorId);
      } else {
        setTerminalOutput(prev => prev + `[ERROR] ${result.error || 'Failed to start planning'}`);
        setIsExecuting(false);
      }
    } catch (error) {
      setTerminalOutput(prev => prev + `[ERROR] ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsExecuting(false);
    }
  }, [task, projectPath]);

  // Handle Research button click
  const handleResearch = useCallback(async () => {
    if (!task || !window.electronAPI?.gsd) return;

    setIsExecuting(true);
    setExecutionType('research');
    setTerminalOutput(`$ /gsd:research-phase ${task.phaseNumber}\n\n`);

    try {
      const result = await window.electronAPI.gsd.researchPhase(projectPath, {
        phaseNumber: task.phaseNumber
      });

      if (result.success && result.data) {
        setGeneratorId(result.data.generatorId);
      } else {
        setTerminalOutput(prev => prev + `[ERROR] ${result.error || 'Failed to start research'}`);
        setIsExecuting(false);
      }
    } catch (error) {
      setTerminalOutput(prev => prev + `[ERROR] ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsExecuting(false);
    }
  }, [task, projectPath]);

  // Handle Execute button click
  const handleExecute = useCallback(async () => {
    if (!task || !task.planPath || !window.electronAPI?.gsd) return;

    setIsExecuting(true);
    setExecutionType('execute');
    setTerminalOutput(`$ /gsd:execute-plan "${task.planPath}"\n\n`);

    try {
      const result = await window.electronAPI.gsd.executePlan(projectPath, {
        planPath: task.planPath
      });

      if (result.success && result.data) {
        setGeneratorId(result.data.generatorId);
      } else {
        setTerminalOutput(prev => prev + `[ERROR] ${result.error || 'Failed to start execution'}`);
        setIsExecuting(false);
      }
    } catch (error) {
      setTerminalOutput(prev => prev + `[ERROR] ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsExecuting(false);
    }
  }, [task, projectPath]);

  // Handle cancel
  const handleCancel = useCallback(async () => {
    if (!generatorId || !window.electronAPI?.gsd) return;

    try {
      await window.electronAPI.gsd.cancelPlan(generatorId);
      setTerminalOutput(prev => prev + '\n\n[CANCELLED]');
      setIsExecuting(false);
    } catch (error) {
      console.error('Failed to cancel:', error);
    }
  }, [generatorId]);

  // Get status badge variant
  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'complete':
        return 'default';
      case 'in_progress':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  if (!task) return null;

  const hasPlan = Boolean(task.planPath);
  const isComplete = task.status === 'complete' || Boolean(task.summaryPath);

  return (
    <div
      className={cn(
        'fixed top-0 right-0 h-full bg-card border-l border-border shadow-xl z-50',
        'w-[500px] flex flex-col',
        'animate-in slide-in-from-right duration-300'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b shrink-0">
        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-semibold truncate">{task.title}</h2>
          <p className="text-sm text-muted-foreground">
            {t('navigation:gsd.phase')} {task.phaseNumber} • {t('navigation:gsd.plan')} {task.id.replace('gsd-', '')}
          </p>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Task metadata */}
      <div className="px-4 py-3 space-y-3 border-b shrink-0">
        {/* Status badges */}
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant={getStatusBadgeVariant(task.status)}>
            {t(`tasks:gsd.status.${task.status}`, task.status)}
          </Badge>
          {task.parallelSafe && (
            <Badge variant="outline" className="gap-1">
              <Zap className="h-3 w-3" />
              {t('navigation:gsd.parallelSafe')}
            </Badge>
          )}
          {hasPlan && (
            <Badge variant="secondary" className="gap-1">
              <FileText className="h-3 w-3" />
              {t('tasks:gsd.hasPlan', 'Has Plan')}
            </Badge>
          )}
          {isComplete && (
            <Badge className="gap-1 bg-green-600">
              <Check className="h-3 w-3" />
              {t('tasks:gsd.complete', 'Complete')}
            </Badge>
          )}
        </div>

        {/* Dependencies */}
        {task.dependsOn.length > 0 && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <LinkIcon className="h-4 w-4" />
            <span>{t('navigation:gsd.dependsOn')}: {task.dependsOn.join(', ')}</span>
          </div>
        )}

        {/* Description */}
        {task.description && (
          <p className="text-sm text-muted-foreground">{task.description}</p>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex gap-2 px-4 py-3 border-b shrink-0">
        <Button
          onClick={handlePlan}
          disabled={isExecuting || hasPlan}
          variant={hasPlan ? 'secondary' : 'default'}
          className="flex-1"
        >
          {executionType === 'plan' && isExecuting ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <FileText className="h-4 w-4 mr-2" />
          )}
          {t('tasks:gsd.actions.plan', 'Plan')}
          {hasPlan && <Check className="h-3 w-3 ml-1" />}
        </Button>

        <Button
          onClick={handleResearch}
          disabled={isExecuting}
          variant="outline"
          className="flex-1"
        >
          {executionType === 'research' && isExecuting ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Search className="h-4 w-4 mr-2" />
          )}
          {t('tasks:gsd.actions.research', 'Research')}
        </Button>

        <Button
          onClick={handleExecute}
          disabled={isExecuting || !hasPlan || isComplete}
          variant={isComplete ? 'secondary' : 'default'}
          className="flex-1"
        >
          {executionType === 'execute' && isExecuting ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Play className="h-4 w-4 mr-2" />
          )}
          {t('tasks:gsd.actions.execute', 'Execute')}
          {isComplete && <Check className="h-3 w-3 ml-1" />}
        </Button>
      </div>

      {/* Cancel button when executing */}
      {isExecuting && (
        <div className="px-4 py-2 border-b shrink-0">
          <Button
            onClick={handleCancel}
            variant="destructive"
            size="sm"
            className="w-full"
          >
            {t('common:buttons.cancel', 'Cancel')}
          </Button>
        </div>
      )}

      {/* Terminal output */}
      <div className="flex-1 overflow-hidden p-4">
        <TerminalOutput
          output={terminalOutput}
          isRunning={isExecuting}
          className="h-full"
        />
      </div>
    </div>
  );
}

export default GsdTaskDetailPanel;
