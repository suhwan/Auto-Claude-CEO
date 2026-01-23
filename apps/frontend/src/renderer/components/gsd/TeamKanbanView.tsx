/**
 * TeamKanbanView Component
 *
 * Displays CEO Teams as kanban lanes with tasks showing progress and status.
 * Part of the GSD (Get Shit Done) workflow UI.
 */

import { useTranslation } from 'react-i18next';
import { ScrollArea, ScrollBar } from '../ui/scroll-area';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Users, CheckCircle2, AlertCircle, Clock, Circle } from 'lucide-react';
import { cn } from '../../lib/utils';
import type {
  GsdSharedBoard,
  GsdTeamLane,
  GsdTeamTask
} from '../../../preload/api/modules/gsd-api';

interface TeamKanbanViewProps {
  board: GsdSharedBoard;
  onTaskClick?: (task: GsdTeamTask) => void;
}

export function TeamKanbanView({ board, onTaskClick }: TeamKanbanViewProps) {
  const { t } = useTranslation(['navigation']);

  if (!board.lanes || board.lanes.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted-foreground">
        <p>{t('navigation:gsd.noKanbanData')}</p>
      </div>
    );
  }

  return (
    <ScrollArea className="w-full">
      <div className="flex gap-4 p-4 min-w-max">
        {board.lanes.map((lane) => (
          <TeamLaneCard
            key={lane.team_id}
            lane={lane}
            onTaskClick={onTaskClick}
          />
        ))}
      </div>
      <ScrollBar orientation="horizontal" />
    </ScrollArea>
  );
}

interface TeamLaneCardProps {
  lane: GsdTeamLane;
  onTaskClick?: (task: GsdTeamTask) => void;
}

function TeamLaneCard({ lane, onTaskClick }: TeamLaneCardProps) {
  const completionPercent = lane.total_tasks > 0
    ? Math.round((lane.completed_tasks / lane.total_tasks) * 100)
    : 0;

  return (
    <Card className="w-64 shrink-0">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            {lane.team_name}
          </span>
          <Badge variant="outline" className="text-xs">
            {lane.completed_tasks}/{lane.total_tasks}
          </Badge>
        </CardTitle>
        <Progress value={completionPercent} className="h-1" />
      </CardHeader>
      <CardContent className="space-y-2">
        {lane.tasks.length === 0 ? (
          <p className="text-xs text-muted-foreground text-center py-4">
            No tasks
          </p>
        ) : (
          lane.tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onClick={() => onTaskClick?.(task)}
            />
          ))
        )}
      </CardContent>
    </Card>
  );
}

interface TaskCardProps {
  task: GsdTeamTask;
  onClick?: () => void;
}

function TaskCard({ task, onClick }: TaskCardProps) {
  const { t } = useTranslation(['navigation']);

  const getStatusIcon = () => {
    switch (task.status) {
      case 'completed':
        return <CheckCircle2 className="h-3 w-3 text-green-500" />;
      case 'in_progress':
        return <Circle className="h-3 w-3 text-blue-500 fill-blue-500" />;
      case 'blocked':
        return <AlertCircle className="h-3 w-3 text-red-500" />;
      case 'waiting':
        return <Clock className="h-3 w-3 text-yellow-500" />;
      default:
        return <Circle className="h-3 w-3 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (task.status) {
      case 'completed': return 'border-l-green-500';
      case 'in_progress': return 'border-l-blue-500';
      case 'blocked': return 'border-l-red-500';
      case 'waiting': return 'border-l-yellow-500';
      default: return 'border-l-gray-300';
    }
  };

  return (
    <div
      className={cn(
        'p-2 rounded border border-l-4 cursor-pointer hover:bg-accent/50 transition-colors',
        getStatusColor()
      )}
      onClick={onClick}
    >
      <div className="flex items-start gap-2">
        {getStatusIcon()}
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium truncate">{task.title}</p>
          {task.progress > 0 && task.status !== 'completed' && (
            <div className="flex items-center gap-2 mt-1">
              <Progress value={task.progress} className="h-1 flex-1" />
              <span className="text-[10px] text-muted-foreground">{task.progress}%</span>
            </div>
          )}
          {task.status === 'blocked' && task.blocking.length > 0 && (
            <p className="text-[10px] text-red-500 mt-1">
              {t('navigation:gsd.blocked')} {task.blocking.length} task(s)
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
