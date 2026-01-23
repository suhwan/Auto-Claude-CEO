import { useTranslation } from 'react-i18next';
import { CheckCircle2, Clock } from 'lucide-react';
import { Badge } from '../ui/badge';
import type { GsdPlanInfo } from '../../../preload/api/modules/gsd-api';

interface RecentActivityProps {
  plans: GsdPlanInfo[];
  limit?: number;
}

export function RecentActivity({ plans, limit = 5 }: RecentActivityProps) {
  const { t } = useTranslation(['navigation', 'common']);

  // Filter completed plans and take recent ones
  const recentCompleted = plans
    .filter(p => p.status === 'complete')
    .slice(-limit)
    .reverse();

  if (recentCompleted.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium flex items-center gap-2">
        <Clock className="h-4 w-4" />
        {t('navigation:gsd.recentCompletions', { defaultValue: 'Recent Completions' })}
      </h4>
      <div className="space-y-1">
        {recentCompleted.map((plan) => (
          <div
            key={plan.id}
            className="flex items-center gap-2 text-sm p-2 rounded bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-900"
          >
            <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
            <span className="flex-1 truncate">{plan.name}</span>
            <Badge variant="outline" className="text-xs">
              {plan.id}
            </Badge>
          </div>
        ))}
      </div>
    </div>
  );
}
