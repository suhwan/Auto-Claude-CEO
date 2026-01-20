import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { ScrollArea } from './ui/scroll-area';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import {
  CheckCircle2, Circle, PlayCircle,
  ChevronDown, ChevronRight, FileText,
  ArrowRight, Loader2, RefreshCw, AlertCircle,
  FolderOpen, Activity, Target, X, Eye, FolderPlus
} from 'lucide-react';
import type {
  GsdRoadmapInfo,
  GsdPhaseInfo,
  GsdPlanInfo,
  GsdStateInfo,
  GsdPlanDetail,
  GsdSharedBoard,
  GsdTeamTask,
  GsdLeaderContext,
  GsdPlanVerification,
  GsdVerificationItem
} from '../../preload/api/modules/gsd-api';
import { TimelineView, ProgressRing, TeamKanbanView, LeaderDashboard, VerificationPanel, NewProjectWizard } from './gsd';
import { Tabs, TabsList, TabsTrigger } from './ui/tabs';

interface GsdViewProps {
  projectPath: string;
}

export function GsdView({ projectPath }: GsdViewProps) {
  const { t } = useTranslation(['navigation', 'common']);
  const [roadmap, setRoadmap] = useState<GsdRoadmapInfo | null>(null);
  const [state, setState] = useState<GsdStateInfo | null>(null);
  const [expandedPhases, setExpandedPhases] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncingPlan, setSyncingPlan] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Plan detail state
  const [planDetail, setPlanDetail] = useState<GsdPlanDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Kanban view state
  const [board, setBoard] = useState<GsdSharedBoard | null>(null);
  const [activeTab, setActiveTab] = useState<'timeline' | 'kanban' | 'dashboard'>('timeline');

  // Leader Context state
  const [leaderContext, setLeaderContext] = useState<GsdLeaderContext | null>(null);

  // Verification state for manual UAT
  const [pendingVerifications, setPendingVerifications] = useState<GsdPlanVerification[]>([]);

  // New Project wizard state
  const [showNewProjectWizard, setShowNewProjectWizard] = useState(false);

  // Load GSD data
  const loadGsdData = useCallback(async () => {
    if (!projectPath) {
      setLoading(false);
      return;
    }

    try {
      setError(null);

      // Load roadmap and state in parallel
      const [roadmapResult, stateResult] = await Promise.all([
        window.electronAPI.gsd.getRoadmap(projectPath),
        window.electronAPI.gsd.getState(projectPath)
      ]);

      if (roadmapResult.success && roadmapResult.data) {
        setRoadmap(roadmapResult.data);
        // Auto-expand current phase
        if (roadmapResult.data.current_phase) {
          setExpandedPhases(new Set([roadmapResult.data.current_phase]));
        }
      } else {
        setError(roadmapResult.error || 'Failed to load roadmap');
      }

      // Load state (optional - don't error if missing)
      if (stateResult.success && stateResult.data) {
        setState(stateResult.data);
      }

      // Load SharedBoard for Kanban view (optional)
      try {
        const boardResult = await window.electronAPI.gsd.getSharedBoard(projectPath);
        if (boardResult.success && boardResult.data) {
          setBoard(boardResult.data);
        }
      } catch {
        // SharedBoard is optional, don't error if missing
        console.debug('SharedBoard not available');
      }

      // Load LeaderContext for Dashboard view (optional)
      try {
        const contextResult = await window.electronAPI.gsd.getLeaderContext(projectPath);
        if (contextResult.success && contextResult.data) {
          setLeaderContext(contextResult.data);
        }
      } catch {
        // LeaderContext is optional, don't error if missing
        console.debug('LeaderContext not available');
      }

      // Load pending verifications for manual UAT
      try {
        const verificationsResult = await window.electronAPI.gsd.getPendingVerifications(projectPath);
        if (verificationsResult.success && verificationsResult.data) {
          setPendingVerifications(verificationsResult.data);
        }
      } catch {
        // Verifications are optional, don't error if missing
        console.debug('Verifications not available');
      }
    } catch (err) {
      console.error('Failed to load GSD data:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [projectPath]);

  // Initial load
  useEffect(() => {
    loadGsdData();
  }, [loadGsdData]);

  // Refresh handler
  const handleRefresh = async () => {
    setRefreshing(true);
    await loadGsdData();
    setRefreshing(false);
  };

  const togglePhase = (phaseNum: number) => {
    const newExpanded = new Set(expandedPhases);
    if (newExpanded.has(phaseNum)) {
      newExpanded.delete(phaseNum);
    } else {
      newExpanded.add(phaseNum);
    }
    setExpandedPhases(newExpanded);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete': return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'in_progress': return <PlayCircle className="h-4 w-4 text-blue-500" />;
      default: return <Circle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'complete':
        return <Badge variant="default" className="bg-green-600">{t('common:labels.complete')}</Badge>;
      case 'in_progress':
        return <Badge variant="secondary">{t('common:labels.inProgress')}</Badge>;
      default:
        return <Badge variant="outline">{t('common:labels.notStarted')}</Badge>;
    }
  };

  const syncPlanToKanban = async (plan: GsdPlanInfo) => {
    if (!projectPath) return;

    try {
      setSyncingPlan(plan.path);

      const result = await window.electronAPI.gsd.syncPlanToKanban(projectPath, plan.path);

      if (result.success && result.data) {
        console.log('Sync result:', result.data);
        // Optionally show a toast notification
      } else {
        console.error('Sync failed:', result.error);
      }
    } catch (error) {
      console.error('Failed to sync to kanban:', error);
    } finally {
      setSyncingPlan(null);
    }
  };

  const syncPhaseToKanban = async (phaseNumber: number) => {
    if (!projectPath) return;

    try {
      setSyncingPlan(`phase-${phaseNumber}`);

      const result = await window.electronAPI.gsd.syncPhaseToKanban(projectPath, phaseNumber);

      if (result.success && result.data) {
        console.log('Phase sync result:', result.data);
      } else {
        console.error('Phase sync failed:', result.error);
      }
    } catch (error) {
      console.error('Failed to sync phase:', error);
    } finally {
      setSyncingPlan(null);
    }
  };

  // Load plan detail handler
  const loadPlanDetail = async (planPath: string) => {
    if (!projectPath) return;

    setLoadingDetail(true);

    try {
      const result = await window.electronAPI.gsd.getPlanDetail(projectPath, planPath);
      if (result.success && result.data) {
        setPlanDetail(result.data);
      }
    } catch (error) {
      console.error('Failed to load plan detail:', error);
    } finally {
      setLoadingDetail(false);
    }
  };

  // Close detail panel
  const closePlanDetail = () => {
    setPlanDetail(null);
  };

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
      <div className="h-full flex flex-col p-4">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error}
          </AlertDescription>
        </Alert>
        <Button variant="outline" className="mt-4 self-start" onClick={handleRefresh}>
          <RefreshCw className="h-4 w-4 mr-2" />
          {t('common:buttons.retry')}
        </Button>
      </div>
    );
  }

  // No roadmap found
  if (!roadmap || roadmap.phases.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <FolderOpen className="h-16 w-16 text-muted-foreground/50 mb-4" />
        <h3 className="text-lg font-medium text-muted-foreground mb-2">
          {t('navigation:gsd.noRoadmap')}
        </h3>
        <p className="text-sm text-muted-foreground text-center max-w-md mb-4">
          {t('navigation:gsd.noRoadmapDescription')}
        </p>
        <div className="flex gap-2">
          <Button onClick={() => setShowNewProjectWizard(true)}>
            <FolderPlus className="h-4 w-4 mr-2" />
            {t('navigation:gsd.newProject')}
          </Button>
          <Button variant="outline" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            {t('common:buttons.refresh')}
          </Button>
        </div>

        <NewProjectWizard
          open={showNewProjectWizard}
          onOpenChange={setShowNewProjectWizard}
          projectPath={projectPath}
          onProjectCreated={loadGsdData}
        />
      </div>
    );
  }

  // Handle task click from Kanban view
  const handleTaskClick = (task: GsdTeamTask) => {
    console.log('Task clicked:', task);
    // TODO: Show task detail modal or navigate to task
  };

  // Verification handlers for manual UAT
  const handleApprove = async (
    planId: string,
    feedback?: string,
    checklist?: GsdVerificationItem[]
  ) => {
    const result = await window.electronAPI.gsd.submitVerification(
      projectPath,
      planId,
      true,
      feedback,
      checklist
    );
    if (result.success) {
      // Refresh data to update verification status
      await loadGsdData();
    } else {
      console.error('Failed to approve:', result.error);
    }
  };

  const handleReject = async (
    planId: string,
    feedback: string,
    checklist?: GsdVerificationItem[]
  ) => {
    const result = await window.electronAPI.gsd.submitVerification(
      projectPath,
      planId,
      false,
      feedback,
      checklist
    );
    if (result.success) {
      // Refresh data to update verification status
      await loadGsdData();
    } else {
      console.error('Failed to reject:', result.error);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header with tabs and progress visualization */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">{t('navigation:gsd.title')}</h2>
          <div className="flex items-center gap-2">
            <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'timeline' | 'kanban' | 'dashboard')}>
              <TabsList className="h-8">
                <TabsTrigger value="timeline" className="text-xs px-3">
                  {t('navigation:gsd.timeline')}
                </TabsTrigger>
                <TabsTrigger value="kanban" className="text-xs px-3">
                  {t('navigation:gsd.teamKanban')}
                </TabsTrigger>
                <TabsTrigger value="dashboard" className="text-xs px-3">
                  {t('navigation:gsd.dashboard')}
                </TabsTrigger>
              </TabsList>
            </Tabs>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>

        {/* Timeline View Tab */}
        {activeTab === 'timeline' && (
          <>
            {/* Progress Summary Row */}
            <div className="flex items-center gap-6 mb-4">
              {/* Progress Ring */}
              <ProgressRing progress={roadmap.progress_percent} size={80}>
                <div className="text-center">
                  <span className="text-xl font-bold">{roadmap.progress_percent}%</span>
                  <div className="text-[10px] text-muted-foreground">
                    {roadmap.phases.filter(p => p.status === 'complete').length}/{roadmap.total_phases}
                  </div>
                </div>
              </ProgressRing>

              {/* Stats Grid */}
              <div className="flex-1 grid grid-cols-3 gap-2 text-center">
                <div>
                  <div className="text-2xl font-bold text-green-600">
                    {roadmap.phases.filter(p => p.status === 'complete').length}
                  </div>
                  <div className="text-xs text-muted-foreground">{t('common:labels.complete')}</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-blue-600">
                    {roadmap.phases.filter(p => p.status === 'in_progress').length}
                  </div>
                  <div className="text-xs text-muted-foreground">{t('common:labels.inProgress')}</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-400">
                    {roadmap.phases.filter(p => p.status === 'not_started').length}
                  </div>
                  <div className="text-xs text-muted-foreground">{t('common:labels.notStarted')}</div>
                </div>
              </div>
            </div>

            {/* Timeline View */}
            <TimelineView
              phases={roadmap.phases}
              currentPhase={roadmap.current_phase}
              onPhaseClick={(phase) => {
                const newExpanded = new Set(expandedPhases);
                if (newExpanded.has(phase.number)) {
                  newExpanded.delete(phase.number);
                } else {
                  newExpanded.add(phase.number);
                }
                setExpandedPhases(newExpanded);

                // Scroll to phase
                document.getElementById(`phase-${phase.number}`)?.scrollIntoView({
                  behavior: 'smooth'
                });
              }}
            />
          </>
        )}

        {/* Kanban View Tab */}
        {activeTab === 'kanban' && board && (
          <TeamKanbanView board={board} onTaskClick={handleTaskClick} />
        )}

        {activeTab === 'kanban' && !board && (
          <div className="flex items-center justify-center h-32 text-muted-foreground">
            <p>{t('navigation:gsd.noKanbanData')}</p>
          </div>
        )}

        {/* Dashboard View Tab */}
        {activeTab === 'dashboard' && leaderContext && (
          <LeaderDashboard context={leaderContext} />
        )}

        {activeTab === 'dashboard' && !leaderContext && (
          <div className="flex items-center justify-center h-32 text-muted-foreground">
            <p>{t('navigation:gsd.noContextData')}</p>
          </div>
        )}
      </div>

      {/* Pending Verifications - Manual UAT */}
      {pendingVerifications.length > 0 && (
        <div className="p-4 border-b bg-blue-50/50 dark:bg-blue-950/20">
          <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
            <Eye className="h-4 w-4 text-blue-500" />
            {t('navigation:gsd.pendingVerifications')} ({pendingVerifications.length})
          </h3>
          <div className="space-y-3">
            {pendingVerifications.map((verification) => (
              <VerificationPanel
                key={verification.plan_id}
                verification={verification}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            ))}
          </div>
        </div>
      )}

      {/* Phase list */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-2">
          {/* State Panel */}
          {state && <StatePanel state={state} />}

          {roadmap.phases.map((phase) => (
            <PhaseCard
              key={phase.number}
              id={`phase-${phase.number}`}
              phase={phase}
              isExpanded={expandedPhases.has(phase.number)}
              onToggle={() => togglePhase(phase.number)}
              onSyncPlan={syncPlanToKanban}
              onSyncPhase={syncPhaseToKanban}
              onPlanClick={loadPlanDetail}
              syncingPlan={syncingPlan}
              getStatusIcon={getStatusIcon}
              getStatusBadge={getStatusBadge}
            />
          ))}
        </div>
      </ScrollArea>

      {/* Plan Detail Modal */}
      {planDetail && (
        <PlanDetailPanel
          plan={planDetail}
          onClose={closePlanDetail}
          loading={loadingDetail}
        />
      )}
    </div>
  );
}

// State Panel Component
interface StatePanelProps {
  state: GsdStateInfo;
}

function StatePanel({ state }: StatePanelProps) {
  const { t } = useTranslation(['navigation', 'common']);

  return (
    <Card className="mb-4">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Activity className="h-4 w-4" />
          {t('navigation:gsd.currentState')}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Current Focus */}
        {state.current_focus && (
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-blue-500" />
            <span className="text-sm font-medium">{state.current_focus}</span>
          </div>
        )}

        {/* Current Position */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-1">
            <span className="text-muted-foreground">{t('navigation:gsd.phase')}:</span>
            <span>{state.current_position.phase}/{state.current_position.total_phases}</span>
            {state.current_position.phase_name && (
              <span className="text-muted-foreground">({state.current_position.phase_name})</span>
            )}
          </div>
          <div className="flex items-center gap-1">
            <span className="text-muted-foreground">{t('navigation:gsd.status')}:</span>
            <Badge variant={state.current_position.status.includes('Ready') ? 'default' : 'secondary'}>
              {state.current_position.status}
            </Badge>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="border-t pt-2">
          <div className="text-xs text-muted-foreground mb-1">{t('navigation:gsd.performance')}</div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="text-center">
              <div className="text-lg font-bold">{state.performance_metrics.total_plans_completed}</div>
              <div className="text-muted-foreground">{t('navigation:gsd.plansCompleted')}</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold">{state.performance_metrics.average_duration || '-'}</div>
              <div className="text-muted-foreground">{t('navigation:gsd.avgDuration')}</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold">{state.performance_metrics.total_execution_time || '-'}</div>
              <div className="text-muted-foreground">{t('navigation:gsd.totalTime')}</div>
            </div>
          </div>
        </div>

        {/* Next Steps */}
        {state.next_steps.length > 0 && (
          <div className="border-t pt-2">
            <div className="text-xs text-muted-foreground mb-1">{t('navigation:gsd.nextSteps')}</div>
            <div className="space-y-1">
              {state.next_steps.slice(0, 2).map((step, i) => (
                <div key={i} className="flex items-center gap-1 text-xs">
                  <ArrowRight className="h-3 w-3 text-green-500" />
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Phase Card Component
interface PhaseCardProps {
  id?: string;
  phase: GsdPhaseInfo;
  isExpanded: boolean;
  onToggle: () => void;
  onSyncPlan: (plan: GsdPlanInfo) => void;
  onSyncPhase: (phaseNumber: number) => void;
  onPlanClick: (planPath: string) => void;
  syncingPlan: string | null;
  getStatusIcon: (status: string) => React.ReactNode;
  getStatusBadge: (status: string) => React.ReactNode;
}

function PhaseCard({
  id,
  phase,
  isExpanded,
  onToggle,
  onSyncPlan,
  onSyncPhase,
  onPlanClick,
  syncingPlan,
  getStatusIcon,
  getStatusBadge
}: PhaseCardProps) {
  const { t } = useTranslation(['navigation', 'common']);

  return (
    <Card id={id} className="overflow-hidden">
      <CardHeader className="p-3">
        <div
          className="flex items-center gap-2 cursor-pointer hover:bg-accent/50 -m-3 p-3 rounded-t-lg"
          onClick={onToggle}
        >
          {isExpanded
            ? <ChevronDown className="h-4 w-4 shrink-0" />
            : <ChevronRight className="h-4 w-4 shrink-0" />
          }
          {getStatusIcon(phase.status)}
          <CardTitle className="text-sm flex-1">
            Phase {phase.number}: {phase.name}
          </CardTitle>
          {getStatusBadge(phase.status)}
          {phase.status !== 'complete' && (
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onSyncPhase(phase.number);
              }}
              disabled={syncingPlan === `phase-${phase.number}`}
              className="ml-2"
            >
              {syncingPlan === `phase-${phase.number}` ? (
                <>
                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                  {t('navigation:gsd.syncing')}
                </>
              ) : (
                <>
                  <ArrowRight className="h-3 w-3 mr-1" />
                  {t('navigation:gsd.syncAll')}
                </>
              )}
            </Button>
          )}
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="p-3 pt-0">
          <p className="text-sm text-muted-foreground mb-3">{phase.goal}</p>

          {/* Progress bar for plans */}
          {phase.total_plans > 0 && (
            <div className="flex items-center gap-2 mb-3">
              <Progress
                value={(phase.completed_plans / phase.total_plans) * 100}
                className="flex-1 h-2"
              />
              <span className="text-xs text-muted-foreground">
                {phase.completed_plans}/{phase.total_plans}
              </span>
            </div>
          )}

          {/* Plans list */}
          <div className="space-y-1">
            {phase.plans.map((plan) => (
              <PlanRow
                key={plan.id}
                plan={plan}
                onSync={() => onSyncPlan(plan)}
                onClick={() => onPlanClick(plan.path)}
                isSyncing={syncingPlan === plan.path}
              />
            ))}
          </div>

          {phase.plans.length === 0 && (
            <p className="text-sm text-muted-foreground italic">
              {t('navigation:gsd.noPlans')}
            </p>
          )}
        </CardContent>
      )}
    </Card>
  );
}

// Plan Row Component
interface PlanRowProps {
  plan: GsdPlanInfo;
  onSync: () => void;
  onClick: () => void;
  isSyncing: boolean;
}

function PlanRow({ plan, onSync, onClick, isSyncing }: PlanRowProps) {
  const { t } = useTranslation(['navigation', 'common']);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete': return 'text-green-500';
      case 'in_progress': return 'text-blue-500';
      default: return 'text-gray-400';
    }
  };

  return (
    <div
      className="flex items-center gap-2 text-sm p-2 rounded hover:bg-accent/30 cursor-pointer"
      onClick={onClick}
    >
      <FileText className={`h-3 w-3 ${getStatusColor(plan.status)}`} />
      <span className="flex-1 truncate">{plan.name}</span>
      {plan.tasks > 0 && (
        <span className="text-muted-foreground text-xs">
          ({plan.completed}/{plan.tasks})
        </span>
      )}
      {plan.status !== 'complete' && (
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onSync();
          }}
          disabled={isSyncing}
          className="h-6 px-2"
        >
          {isSyncing ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <>
              <ArrowRight className="h-3 w-3 mr-1" />
              {t('navigation:gsd.kanban')}
            </>
          )}
        </Button>
      )}
    </div>
  );
}

// Plan Detail Panel Component (Modal)
interface PlanDetailPanelProps {
  plan: GsdPlanDetail;
  onClose: () => void;
  loading?: boolean;
}

function PlanDetailPanel({ plan, onClose, loading }: PlanDetailPanelProps) {
  const { t } = useTranslation(['navigation', 'common']);

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <Card
        className="w-[600px] max-h-[80vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div>
            <CardTitle className="text-lg">
              Plan {plan.id}: {plan.name}
            </CardTitle>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline">~{plan.estimated_minutes} min</Badge>
              {plan.parallel_safe && <Badge variant="secondary">Parallel Safe</Badge>}
              {plan.depends_on && <Badge variant="outline">{t('navigation:gsd.dependsOn')}: {plan.depends_on}</Badge>}
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>

        <ScrollArea className="flex-1 px-6 pb-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              {/* Objective */}
              {plan.objective && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium mb-1">{t('navigation:gsd.objective')}</h4>
                  <p className="text-sm text-muted-foreground">{plan.objective}</p>
                </div>
              )}

              {/* Tasks */}
              {plan.tasks.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium mb-2">
                    {t('navigation:gsd.tasks')} ({plan.tasks.length})
                  </h4>
                  <div className="space-y-2">
                    {plan.tasks.map((task) => (
                      <div
                        key={task.id}
                        className="flex items-start gap-2 p-2 rounded border"
                      >
                        <div className={`mt-0.5 ${task.completed ? 'text-green-500' : 'text-gray-400'}`}>
                          {task.completed ? <CheckCircle2 className="h-4 w-4" /> : <Circle className="h-4 w-4" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium">{task.name}</span>
                            <Badge variant="outline" className="text-xs">{task.type}</Badge>
                          </div>
                          {task.files.length > 0 && (
                            <div className="text-xs text-muted-foreground mt-1">
                              {task.files.join(', ')}
                            </div>
                          )}
                          {task.done_criteria && (
                            <div className="text-xs text-green-600 mt-1">
                              {task.done_criteria}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Success Criteria */}
              {plan.success_criteria.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium mb-2">{t('navigation:gsd.successCriteria')}</h4>
                  <div className="space-y-1">
                    {plan.success_criteria.map((criteria, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm">
                        <Circle className="h-3 w-3 text-gray-400" />
                        <span>{criteria}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Output Files */}
              {plan.output_files.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium mb-2">{t('navigation:gsd.outputFiles')}</h4>
                  <div className="flex flex-wrap gap-1">
                    {plan.output_files.map((file, i) => (
                      <Badge key={i} variant="secondary" className="text-xs font-mono">
                        {file}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Verification */}
              {plan.verification && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium mb-1">{t('navigation:gsd.verification')}</h4>
                  <pre className="text-xs bg-muted p-2 rounded overflow-x-auto whitespace-pre-wrap">
                    {plan.verification}
                  </pre>
                </div>
              )}
            </>
          )}
        </ScrollArea>
      </Card>
    </div>
  );
}
