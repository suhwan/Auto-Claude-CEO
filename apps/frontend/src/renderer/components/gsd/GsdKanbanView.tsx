/**
 * GsdKanbanView - Phase-grouped Kanban board for GSD tasks
 *
 * Displays GSD ROADMAP phases as swimlanes with tasks grouped by status.
 * Each phase row shows its plans as cards that can be tracked through
 * Pending -> In Progress -> Complete statuses.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { ScrollArea, ScrollBar } from '../ui/scroll-area';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '../ui/tooltip';
import {
  CheckCircle2, Circle, PlayCircle, Loader2, RefreshCw,
  ChevronRight, ChevronDown, Play, Link as LinkIcon,
  AlertCircle
} from 'lucide-react';
import type {
  GsdConvertedTask,
  GsdPhaseGroup,
  GsdTaskConversionResult
} from '../../../preload/api/modules/gsd-api';

// Task status columns for Kanban
type KanbanColumn = 'pending' | 'in_progress' | 'complete';

interface GsdKanbanViewProps {
  projectPath: string;
  onTaskClick?: (task: GsdConvertedTask) => void;
  onExecutePlan?: (taskId: string) => void;
}

export function GsdKanbanView({ projectPath, onTaskClick, onExecutePlan }: GsdKanbanViewProps) {
  const { t } = useTranslation(['tasks', 'common', 'navigation']);
  const [data, setData] = useState<GsdTaskConversionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set());
  const [refreshing, setRefreshing] = useState(false);

  // Load GSD Kanban data
  const loadData = useCallback(async () => {
    if (!projectPath) {
      setLoading(false);
      return;
    }

    try {
      setError(null);
      const result = await window.electronAPI.gsd.getKanbanTasks(projectPath);

      if (result.success && result.data) {
        setData(result.data);
        // Auto-expand phases with in-progress tasks
        const phasesWithInProgress = result.data.phases
          .filter(p => result.data.tasks.some(t =>
            p.tasks.includes(t.id) && t.status === 'in_progress'
          ))
          .map(p => p.id);
        setExpandedPhases(new Set(phasesWithInProgress));
      } else {
        setError(result.error || 'Failed to load GSD Kanban data');
      }
    } catch (err) {
      console.error('Failed to load GSD Kanban data:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [projectPath]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const togglePhase = (phaseId: string) => {
    setExpandedPhases(prev => {
      const newSet = new Set(prev);
      if (newSet.has(phaseId)) {
        newSet.delete(phaseId);
      } else {
        newSet.add(phaseId);
      }
      return newSet;
    });
  };

  // Get tasks by status for a phase
  const getTasksByStatus = useCallback((phase: GsdPhaseGroup, status: KanbanColumn) => {
    if (!data) return [];
    return data.tasks.filter(task =>
      phase.tasks.includes(task.id) && task.status === status
    );
  }, [data]);

  // Get column header
  const getColumnHeader = (status: KanbanColumn): string => {
    switch (status) {
      case 'pending':
        return t('navigation:gsd.kanban.pending');
      case 'in_progress':
        return t('navigation:gsd.kanban.inProgress');
      case 'complete':
        return t('navigation:gsd.kanban.complete');
    }
  };

  // Get column icon
  const getColumnIcon = (status: KanbanColumn) => {
    switch (status) {
      case 'pending':
        return <Circle className="h-4 w-4 text-gray-400" />;
      case 'in_progress':
        return <PlayCircle className="h-4 w-4 text-blue-500" />;
      case 'complete':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    }
  };

  // Calculate phase progress
  const getPhaseProgress = useCallback((phase: GsdPhaseGroup) => {
    if (!data) return { completed: 0, total: 0, percent: 0 };
    const phaseTasks = data.tasks.filter(t => phase.tasks.includes(t.id));
    const completed = phaseTasks.filter(t => t.status === 'complete').length;
    const total = phaseTasks.length;
    const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
    return { completed, total, percent };
  }, [data]);

  // Loading state
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="text-sm text-muted-foreground">{t('common:labels.loading')}</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-4">
        <AlertCircle className="h-12 w-12 text-destructive mb-4" />
        <p className="text-sm text-destructive mb-4">{error}</p>
        <Button variant="outline" onClick={handleRefresh}>
          <RefreshCw className="h-4 w-4 mr-2" />
          {t('common:buttons.retry')}
        </Button>
      </div>
    );
  }

  // No data state
  if (!data || data.phases.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-4">
        <p className="text-sm text-muted-foreground mb-4">
          {t('navigation:gsd.noRoadmap')}
        </p>
        <Button variant="outline" onClick={handleRefresh}>
          <RefreshCw className="h-4 w-4 mr-2" />
          {t('common:buttons.refresh')}
        </Button>
      </div>
    );
  }

  const columns: KanbanColumn[] = ['pending', 'in_progress', 'complete'];

  return (
    <TooltipProvider>
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <h3 className="text-lg font-semibold">{t('navigation:gsd.phaseKanban')}</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {/* Kanban Board with horizontal scroll */}
        <ScrollArea className="flex-1">
          <div className="p-4">
            {/* Column Headers */}
            <div className="flex gap-4 mb-4 min-w-[900px]">
              <div className="w-48 shrink-0" /> {/* Phase name column */}
              {columns.map(col => (
                <div key={col} className="flex-1 min-w-[250px]">
                  <div className="flex items-center gap-2 px-3 py-2 bg-muted/50 rounded-t-lg">
                    {getColumnIcon(col)}
                    <span className="text-sm font-medium">{getColumnHeader(col)}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Phase Swimlanes */}
            <div className="space-y-2">
              {data.phases.map(phase => {
                const isExpanded = expandedPhases.has(phase.id);
                const progress = getPhaseProgress(phase);

                return (
                  <div key={phase.id} className="border rounded-lg overflow-hidden">
                    {/* Phase Header Row */}
                    <div
                      className="flex items-center gap-4 p-3 bg-muted/30 cursor-pointer hover:bg-muted/50"
                      onClick={() => togglePhase(phase.id)}
                    >
                      {/* Phase Name Column */}
                      <div className="w-48 shrink-0 flex items-center gap-2">
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                        <span className="font-medium text-sm truncate">{phase.name}</span>
                      </div>

                      {/* Phase Progress Summary */}
                      <div className="flex-1 flex items-center gap-4 min-w-[750px]">
                        {columns.map(col => {
                          const tasks = getTasksByStatus(phase, col);
                          return (
                            <div key={col} className="flex-1 min-w-[250px]">
                              <Badge variant={col === 'complete' ? 'default' : 'secondary'}>
                                {tasks.length} {t('navigation:gsd.plans')}
                              </Badge>
                            </div>
                          );
                        })}
                      </div>

                      {/* Overall Progress */}
                      <div className="w-24 text-right">
                        <Badge
                          variant={progress.percent === 100 ? 'default' : 'outline'}
                          className={progress.percent === 100 ? 'bg-green-600' : ''}
                        >
                          {progress.percent}%
                        </Badge>
                      </div>
                    </div>

                    {/* Expanded Tasks */}
                    {isExpanded && (
                      <div className="flex gap-4 p-4 min-w-[900px]">
                        {/* Empty phase name spacer */}
                        <div className="w-48 shrink-0" />

                        {/* Task Columns */}
                        {columns.map(col => (
                          <div key={col} className="flex-1 min-w-[250px] space-y-2">
                            {getTasksByStatus(phase, col).map(task => (
                              <TaskCard
                                key={task.id}
                                task={task}
                                onClick={() => onTaskClick?.(task)}
                                onExecute={onExecutePlan ? () => onExecutePlan(task.id) : undefined}
                              />
                            ))}
                            {getTasksByStatus(phase, col).length === 0 && (
                              <div className="p-4 text-center text-xs text-muted-foreground border border-dashed rounded-lg">
                                {t('navigation:gsd.kanban.empty')}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
          <ScrollBar orientation="horizontal" />
        </ScrollArea>
      </div>
    </TooltipProvider>
  );
}

// Task Card Component
interface TaskCardProps {
  task: GsdConvertedTask;
  onClick?: () => void;
  onExecute?: () => void;
}

function TaskCard({ task, onClick, onExecute }: TaskCardProps) {
  const { t } = useTranslation(['navigation', 'common']);

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={onClick}
    >
      <CardContent className="p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-medium truncate">{task.title}</h4>
            {task.description && (
              <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                {task.description}
              </p>
            )}
          </div>
        </div>

        {/* Task metadata */}
        <div className="flex items-center gap-2 mt-2 flex-wrap">
          <Badge variant="outline" className="text-xs">
            {task.id}
          </Badge>
          {task.parallelSafe && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Badge variant="secondary" className="text-xs">
                  {t('navigation:gsd.parallelSafe')}
                </Badge>
              </TooltipTrigger>
              <TooltipContent>
                {t('navigation:gsd.parallelSafeTooltip')}
              </TooltipContent>
            </Tooltip>
          )}
          {task.dependsOn.length > 0 && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Badge variant="outline" className="text-xs">
                  <LinkIcon className="h-3 w-3 mr-1" />
                  {task.dependsOn.length}
                </Badge>
              </TooltipTrigger>
              <TooltipContent>
                {t('navigation:gsd.dependsOn')}: {task.dependsOn.join(', ')}
              </TooltipContent>
            </Tooltip>
          )}
        </div>

        {/* Execute button for non-complete tasks */}
        {task.status !== 'complete' && onExecute && (
          <Button
            variant="outline"
            size="sm"
            className="w-full mt-2"
            onClick={(e) => {
              e.stopPropagation();
              onExecute();
            }}
          >
            <Play className="h-3 w-3 mr-1" />
            {t('navigation:gsd.execute')}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

export default GsdKanbanView;
