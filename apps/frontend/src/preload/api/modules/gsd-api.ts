/**
 * GSD (Get Shit Done) Preload API
 *
 * Exposes GSD workflow operations to the renderer process
 */

import { IPC_CHANNELS } from '../../../shared/constants';
import type { IPCResult } from '../../../shared/types';
import { invokeIpc } from './ipc-utils';

/**
 * GSD Roadmap information
 */
export interface GsdRoadmapInfo {
  phases: GsdPhaseInfo[];
  current_phase: number;
  total_phases: number;
  progress_percent: number;
}

/**
 * GSD Phase information
 */
export interface GsdPhaseInfo {
  number: number;
  name: string;
  goal: string;
  status: 'complete' | 'in_progress' | 'not_started';
  depends_on?: number;
  plans: GsdPlanInfo[];
  completed_plans: number;
  total_plans: number;
}

/**
 * GSD Plan information
 */
export interface GsdPlanInfo {
  id: string;
  name: string;
  path: string;
  tasks: number;
  completed: number;
  status: 'complete' | 'in_progress' | 'not_started';
}

/**
 * GSD Sync result
 */
export interface GsdSyncResult {
  success: boolean;
  tasks?: GsdTask[];
  error?: string;
  task_count?: number;
}

/**
 * GSD Task
 */
export interface GsdTask {
  id: string;
  title: string;
  description: string;
  status: string;
  phase: string;
  plan: string;
  task_number: number;
  files: string[];
  action: string;
  verify: string;
  done_criteria: string;
  gsd_task_type: string;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
}

/**
 * GSD Progress information
 */
export interface GsdProgressInfo {
  total_phases: number;
  completed_phases: number;
  percent: number;
  current_phase: number;
}

/**
 * GSD Sync status
 */
export interface GsdSyncStatus {
  synced_tasks: number;
  pending_tasks: number;
  completed_tasks: number;
  last_sync: string | null;
}

/**
 * GSD State information (from STATE.md)
 */
export interface GsdStateInfo {
  current_focus: string;
  current_position: {
    phase: number;
    total_phases: number;
    phase_name: string;
    status: string;
    plan_progress: string;
  };
  performance_metrics: {
    total_plans_completed: number;
    average_duration: string;
    total_execution_time: string;
  };
  recent_trend: string[];
  session_continuity: {
    last_session: string;
    stopped_at: string;
    resume_file: string | null;
  };
  next_steps: string[];
}

/**
 * GSD Plan detail information (from PLAN.md)
 */
export interface GsdPlanDetail {
  id: string;
  name: string;
  phase: number;
  plan: number;
  path: string;
  estimated_minutes: number;
  parallel_safe: boolean;
  depends_on?: string;
  objective: string;
  context: string;
  tasks: GsdTaskDetail[];
  verification: string;
  success_criteria: string[];
  output_files: string[];
}

/**
 * GSD Task detail information
 */
export interface GsdTaskDetail {
  id: string;
  type: string;
  name: string;
  files: string[];
  action: string;
  verify: string;
  done_criteria: string;
  completed: boolean;
}

/**
 * GSD Team Task (for SharedBoard/Kanban)
 */
export interface GsdTeamTask {
  id: string;
  team_id: string;
  title: string;
  description: string;
  status: 'not_started' | 'in_progress' | 'blocked' | 'waiting' | 'completed';
  progress: number;
  depends_on: string[];
  blocking: string[];
  assignee?: string;
  priority: number;
}

/**
 * GSD Team Lane (for SharedBoard/Kanban)
 */
export interface GsdTeamLane {
  team_id: string;
  team_name: string;
  tasks: GsdTeamTask[];
  total_tasks: number;
  completed_tasks: number;
  blocked_tasks: number;
}

/**
 * GSD Shared Board (for CEO Team Kanban)
 */
export interface GsdSharedBoard {
  id: string;
  name: string;
  phase: number;
  lanes: GsdTeamLane[];
  created_at: string;
  updated_at: string;
}

/**
 * GSD Goal (for Leader Dashboard)
 */
export interface GsdGoal {
  id: string;
  title: string;
  description: string;
  priority: 'primary' | 'secondary' | 'tertiary';
  status: 'active' | 'achieved' | 'abandoned';
  phase?: number;
}

/**
 * GSD Decision (for Leader Dashboard)
 */
export interface GsdDecision {
  id: string;
  title: string;
  description: string;
  rationale: string;
  made_at: string;
  phase?: number;
}

/**
 * GSD Pattern (for Leader Dashboard)
 */
export interface GsdPattern {
  id: string;
  name: string;
  description: string;
  category: string;
  occurrences: number;
}

/**
 * GSD Mistake (for Leader Dashboard)
 */
export interface GsdMistake {
  id: string;
  description: string;
  impact: string;
  lesson_learned: string;
  occurred_at: string;
  phase?: number;
}

/**
 * GSD Risk (for Leader Dashboard)
 */
export interface GsdRisk {
  id: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  likelihood: 'unlikely' | 'possible' | 'likely' | 'certain';
  mitigation?: string;
  status: 'identified' | 'mitigated' | 'occurred' | 'closed';
}

/**
 * GSD Leader Context (for CEO Dashboard)
 */
export interface GsdLeaderContext {
  project_id: string;
  phase: number;
  goals: GsdGoal[];
  decisions: GsdDecision[];
  patterns: GsdPattern[];
  mistakes: GsdMistake[];
  risks: GsdRisk[];
  updated_at: string;
}

/**
 * Verification status for manual UAT
 */
export type VerificationStatus = 'pending' | 'approved' | 'rejected' | 'not_required';

/**
 * Verification checklist item
 */
export interface GsdVerificationItem {
  id: string;
  description: string;
  checked: boolean;
}

/**
 * Plan verification info for manual UAT
 */
export interface GsdPlanVerification {
  plan_id: string;
  plan_name: string;
  phase: number;
  auto_qa_passed: boolean;
  verification_status: VerificationStatus;
  checklist: GsdVerificationItem[];
  feedback?: string;
  verified_at?: string;
}

/**
 * Input for creating a new GSD project
 */
export interface CreateProjectInput {
  name: string;
  description: string;
  coreValue?: string;
}

/**
 * Input for generating a roadmap
 */
export interface GenerateRoadmapInput {
  goals: string;
  depth: 'quick' | 'standard' | 'comprehensive';
}

/**
 * Result of creating a new GSD project
 */
export interface CreateProjectResult {
  success: boolean;
  projectPath: string;
  filesCreated: string[];
  error?: string;
}

/**
 * GSD API interface
 */
export interface GsdAPI {
  getRoadmap: (projectPath: string, roadmapPath?: string) => Promise<IPCResult<GsdRoadmapInfo>>;
  getState: (projectPath: string, statePath?: string) => Promise<IPCResult<GsdStateInfo | null>>;
  getPlanDetail: (projectPath: string, planPath: string) => Promise<IPCResult<GsdPlanDetail | null>>;
  getPhaseProgress: (projectPath: string, roadmapPath?: string) => Promise<IPCResult<GsdProgressInfo>>;
  syncPlanToKanban: (projectPath: string, planPath: string) => Promise<IPCResult<GsdSyncResult>>;
  syncPhaseToKanban: (projectPath: string, phaseNumber: number) => Promise<IPCResult<GsdSyncResult>>;
  updateTaskStatus: (projectPath: string, taskId: string, status: string) => Promise<IPCResult<{ success: boolean }>>;
  generateSummary: (projectPath: string, planPath: string) => Promise<IPCResult<{ summaryPath: string | null }>>;
  getSyncStatus: (projectPath: string) => Promise<IPCResult<GsdSyncStatus>>;
  getSharedBoard: (projectPath: string, phase?: number) => Promise<IPCResult<GsdSharedBoard | null>>;
  getLeaderContext: (projectPath: string, phase?: number) => Promise<IPCResult<GsdLeaderContext | null>>;
  getPendingVerifications: (projectPath: string) => Promise<IPCResult<GsdPlanVerification[]>>;
  submitVerification: (
    projectPath: string,
    planId: string,
    approved: boolean,
    feedback?: string,
    checklist?: GsdVerificationItem[]
  ) => Promise<IPCResult<void>>;
  createProject: (projectPath: string, input: CreateProjectInput) => Promise<IPCResult<CreateProjectResult>>;
  generateRoadmap: (projectPath: string, input: GenerateRoadmapInput) => Promise<IPCResult<{ generatorId: string }>>;
  cancelGeneration: (generatorId: string) => Promise<IPCResult<void>>;
  onRoadmapOutput: (callback: (data: { generatorId: string; data: string }) => void) => () => void;
  onRoadmapError: (callback: (data: { generatorId: string; error: string }) => void) => () => void;
  onRoadmapComplete: (callback: (data: { generatorId: string; success: boolean }) => void) => () => void;
}

/**
 * Create GSD API implementation
 */
export const createGsdAPI = (): GsdAPI => ({
  getRoadmap: (projectPath: string, roadmapPath?: string): Promise<IPCResult<GsdRoadmapInfo>> =>
    invokeIpc(IPC_CHANNELS.GSD_GET_ROADMAP, projectPath, roadmapPath),

  getState: (projectPath: string, statePath?: string): Promise<IPCResult<GsdStateInfo | null>> =>
    invokeIpc(IPC_CHANNELS.GSD_GET_STATE, projectPath, statePath),

  getPlanDetail: (projectPath: string, planPath: string): Promise<IPCResult<GsdPlanDetail | null>> =>
    invokeIpc(IPC_CHANNELS.GSD_GET_PLAN_DETAIL, projectPath, planPath),

  getPhaseProgress: (projectPath: string, roadmapPath?: string): Promise<IPCResult<GsdProgressInfo>> =>
    invokeIpc(IPC_CHANNELS.GSD_GET_PHASE_PROGRESS, projectPath, roadmapPath),

  syncPlanToKanban: (projectPath: string, planPath: string): Promise<IPCResult<GsdSyncResult>> =>
    invokeIpc(IPC_CHANNELS.GSD_SYNC_PLAN_TO_KANBAN, projectPath, planPath),

  syncPhaseToKanban: (projectPath: string, phaseNumber: number): Promise<IPCResult<GsdSyncResult>> =>
    invokeIpc(IPC_CHANNELS.GSD_SYNC_PHASE_TO_KANBAN, projectPath, phaseNumber),

  updateTaskStatus: (projectPath: string, taskId: string, status: string): Promise<IPCResult<{ success: boolean }>> =>
    invokeIpc(IPC_CHANNELS.GSD_UPDATE_TASK_STATUS, projectPath, taskId, status),

  generateSummary: (projectPath: string, planPath: string): Promise<IPCResult<{ summaryPath: string | null }>> =>
    invokeIpc(IPC_CHANNELS.GSD_GENERATE_SUMMARY, projectPath, planPath),

  getSyncStatus: (projectPath: string): Promise<IPCResult<GsdSyncStatus>> =>
    invokeIpc(IPC_CHANNELS.GSD_GET_SYNC_STATUS, projectPath),

  getSharedBoard: (projectPath: string, phase?: number): Promise<IPCResult<GsdSharedBoard | null>> =>
    invokeIpc(IPC_CHANNELS.GSD_GET_SHARED_BOARD, projectPath, phase),

  getLeaderContext: (projectPath: string, phase?: number): Promise<IPCResult<GsdLeaderContext | null>> =>
    invokeIpc(IPC_CHANNELS.GSD_GET_LEADER_CONTEXT, projectPath, phase),

  getPendingVerifications: (projectPath: string): Promise<IPCResult<GsdPlanVerification[]>> =>
    invokeIpc(IPC_CHANNELS.GSD_GET_PENDING_VERIFICATIONS, projectPath),

  submitVerification: (
    projectPath: string,
    planId: string,
    approved: boolean,
    feedback?: string,
    checklist?: GsdVerificationItem[]
  ): Promise<IPCResult<void>> =>
    invokeIpc(IPC_CHANNELS.GSD_SUBMIT_VERIFICATION, projectPath, planId, approved, feedback, checklist),

  createProject: (projectPath: string, input: CreateProjectInput): Promise<IPCResult<CreateProjectResult>> =>
    invokeIpc(IPC_CHANNELS.GSD_CREATE_PROJECT, projectPath, input),

  generateRoadmap: (projectPath: string, input: GenerateRoadmapInput): Promise<IPCResult<{ generatorId: string }>> =>
    invokeIpc(IPC_CHANNELS.GSD_GENERATE_ROADMAP, projectPath, input),

  cancelGeneration: (generatorId: string): Promise<IPCResult<void>> =>
    invokeIpc(IPC_CHANNELS.GSD_CANCEL_GENERATION, generatorId),

  onRoadmapOutput: (callback: (data: { generatorId: string; data: string }) => void): (() => void) => {
    const handler = (_: unknown, data: { generatorId: string; data: string }) => callback(data);
    window.electronAPI?.ipcRenderer?.on('gsd:roadmap-output', handler);
    return () => window.electronAPI?.ipcRenderer?.off('gsd:roadmap-output', handler);
  },

  onRoadmapError: (callback: (data: { generatorId: string; error: string }) => void): (() => void) => {
    const handler = (_: unknown, data: { generatorId: string; error: string }) => callback(data);
    window.electronAPI?.ipcRenderer?.on('gsd:roadmap-error', handler);
    return () => window.electronAPI?.ipcRenderer?.off('gsd:roadmap-error', handler);
  },

  onRoadmapComplete: (callback: (data: { generatorId: string; success: boolean }) => void): (() => void) => {
    const handler = (_: unknown, data: { generatorId: string; success: boolean }) => callback(data);
    window.electronAPI?.ipcRenderer?.on('gsd:roadmap-complete', handler);
    return () => window.electronAPI?.ipcRenderer?.off('gsd:roadmap-complete', handler);
  }
});
