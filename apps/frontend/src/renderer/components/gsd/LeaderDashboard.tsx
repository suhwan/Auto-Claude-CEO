/**
 * LeaderDashboard Component
 *
 * Displays leader context information including goals, decisions,
 * patterns, mistakes, and risks in a dashboard layout.
 * Part of the GSD (Get Shit Done) workflow UI.
 */

import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import {
  Target, FileText, AlertTriangle, RefreshCw, XCircle,
  CheckCircle2, TrendingUp
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type {
  GsdLeaderContext,
  GsdGoal,
  GsdDecision,
  GsdPattern,
  GsdMistake,
  GsdRisk
} from '../../../preload/api/modules/gsd-api';

interface LeaderDashboardProps {
  context: GsdLeaderContext;
}

export function LeaderDashboard({ context }: LeaderDashboardProps) {
  return (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          {/* Goals Card */}
          <GoalsCard goals={context.goals} />

          {/* Decisions Card */}
          <DecisionsCard decisions={context.decisions} />

          {/* Risks Card */}
          <RisksCard risks={context.risks} />

          {/* Patterns Card */}
          <PatternsCard patterns={context.patterns} />
        </div>

        {/* Mistakes Card (full width) */}
        {context.mistakes.length > 0 && (
          <MistakesCard mistakes={context.mistakes} />
        )}
      </div>
    </ScrollArea>
  );
}

interface GoalsCardProps {
  goals: GsdGoal[];
}

function GoalsCard({ goals }: GoalsCardProps) {
  const { t } = useTranslation(['navigation']);
  const activeGoals = goals.filter(g => g.status === 'active');

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Target className="h-4 w-4 text-blue-500" />
          {t('navigation:gsd.goals')}
          <Badge variant="outline" className="ml-auto text-xs">
            {activeGoals.length} {t('navigation:gsd.active')}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {goals.length === 0 ? (
          <p className="text-xs text-muted-foreground">{t('navigation:gsd.noGoals')}</p>
        ) : (
          goals.slice(0, 5).map((goal) => (
            <div key={goal.id} className="flex items-start gap-2">
              <Badge
                variant={goal.priority === 'primary' ? 'default' : 'secondary'}
                className="text-[10px] shrink-0"
              >
                {goal.priority}
              </Badge>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">{goal.title}</p>
                {goal.status === 'achieved' && (
                  <CheckCircle2 className="h-3 w-3 text-green-500 inline ml-1" />
                )}
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

interface DecisionsCardProps {
  decisions: GsdDecision[];
}

function DecisionsCard({ decisions }: DecisionsCardProps) {
  const { t } = useTranslation(['navigation']);
  const recentDecisions = decisions.slice(-5).reverse();

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <FileText className="h-4 w-4 text-purple-500" />
          {t('navigation:gsd.decisions')}
          <Badge variant="outline" className="ml-auto text-xs">
            {decisions.length} {t('navigation:gsd.total')}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {decisions.length === 0 ? (
          <p className="text-xs text-muted-foreground">{t('navigation:gsd.noDecisions')}</p>
        ) : (
          recentDecisions.map((decision) => (
            <div key={decision.id} className="text-xs">
              <p className="font-medium truncate">{decision.title}</p>
              {decision.rationale && (
                <p className="text-muted-foreground truncate">{decision.rationale}</p>
              )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

interface RisksCardProps {
  risks: GsdRisk[];
}

function RisksCard({ risks }: RisksCardProps) {
  const { t } = useTranslation(['navigation']);
  const activeRisks = risks.filter(r => r.status === 'identified');

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50 dark:bg-red-950';
      case 'high': return 'text-orange-600 bg-orange-50 dark:bg-orange-950';
      case 'medium': return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-950';
      default: return 'text-gray-600 bg-gray-50 dark:bg-gray-900';
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-orange-500" />
          {t('navigation:gsd.risks')}
          <Badge variant="outline" className="ml-auto text-xs">
            {activeRisks.length} {t('navigation:gsd.active')}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {risks.length === 0 ? (
          <p className="text-xs text-muted-foreground">{t('navigation:gsd.noRisks')}</p>
        ) : (
          risks.slice(0, 5).map((risk) => (
            <div key={risk.id} className="flex items-start gap-2">
              <Badge
                variant="outline"
                className={cn('text-[10px] shrink-0', getSeverityColor(risk.severity))}
              >
                {risk.severity}
              </Badge>
              <p className="text-xs truncate flex-1">{risk.title}</p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

interface PatternsCardProps {
  patterns: GsdPattern[];
}

function PatternsCard({ patterns }: PatternsCardProps) {
  const { t } = useTranslation(['navigation']);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <RefreshCw className="h-4 w-4 text-green-500" />
          {t('navigation:gsd.patterns')}
          <Badge variant="outline" className="ml-auto text-xs">
            {patterns.length} {t('navigation:gsd.found')}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {patterns.length === 0 ? (
          <p className="text-xs text-muted-foreground">{t('navigation:gsd.noPatterns')}</p>
        ) : (
          patterns.slice(0, 5).map((pattern) => (
            <div key={pattern.id} className="flex items-center gap-2">
              <TrendingUp className="h-3 w-3 text-muted-foreground shrink-0" />
              <p className="text-xs truncate flex-1">{pattern.name}</p>
              {pattern.occurrences > 1 && (
                <Badge variant="secondary" className="text-[10px]">
                  x{pattern.occurrences}
                </Badge>
              )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

interface MistakesCardProps {
  mistakes: GsdMistake[];
}

function MistakesCard({ mistakes }: MistakesCardProps) {
  const { t } = useTranslation(['navigation']);
  const recentMistakes = mistakes.slice(-3).reverse();

  return (
    <Card className="border-red-200 dark:border-red-900">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <XCircle className="h-4 w-4 text-red-500" />
          {t('navigation:gsd.recentMistakes')}
          <Badge variant="outline" className="ml-auto text-xs text-red-600">
            {mistakes.length} {t('navigation:gsd.total')}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {recentMistakes.map((mistake) => (
          <div key={mistake.id} className="text-xs border-l-2 border-red-300 dark:border-red-700 pl-2">
            <p className="font-medium">{mistake.description}</p>
            {mistake.lesson_learned && (
              <p className="text-green-600 dark:text-green-400 mt-1">
                {t('navigation:gsd.lesson')}: {mistake.lesson_learned}
              </p>
            )}
            {mistake.occurred_at && (
              <p className="text-muted-foreground text-[10px] mt-1">
                {new Date(mistake.occurred_at).toLocaleDateString()}
              </p>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
