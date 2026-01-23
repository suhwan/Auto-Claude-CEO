/**
 * CEO (Chief Executive Officer) Agent Preload API
 *
 * Exposes CEO agent and routing operations to the renderer process
 */

import { IPC_CHANNELS } from '../../../shared/constants';
import type { IPCResult } from '../../../shared/types';
import { invokeIpc } from './ipc-utils';

/**
 * Task type classification
 */
export type TaskType = 'coding' | 'non_coding' | 'mixed';

/**
 * Agent definition
 */
export interface AgentDefinition {
  name: string;
  description: string;
  tools: string[];
  model: string;
  skills: string;
  permission_mode: string;
  team: string;
  role: string;
  content: string;
}

/**
 * Team information
 */
export interface TeamInfo {
  name: string;
  description: string;
  leader: AgentDefinition | null;
  members: AgentDefinition[];
}

/**
 * Routing result
 */
export interface RoutingResult {
  task_type: TaskType;
  target: string;
  confidence: number;
  keywords_matched: string[];
}

/**
 * Loaded agents data
 */
export interface LoadedAgentsData {
  agents: Record<string, AgentDefinition>;
  teams: Record<string, TeamInfo>;
}

/**
 * CEO API interface
 */
export interface CeoAPI {
  loadAgents: (projectPath: string) => Promise<IPCResult<LoadedAgentsData>>;
  getAgent: (projectPath: string, agentName: string) => Promise<IPCResult<AgentDefinition | null>>;
  getTeams: (projectPath: string) => Promise<IPCResult<Record<string, TeamInfo>>>;
  classifyTask: (projectPath: string, request: string) => Promise<IPCResult<RoutingResult>>;
  routeTask: (projectPath: string, request: string) => Promise<IPCResult<RoutingResult>>;
}

/**
 * Create CEO API implementation
 */
export const createCeoAPI = (): CeoAPI => ({
  loadAgents: (projectPath: string): Promise<IPCResult<LoadedAgentsData>> =>
    invokeIpc(IPC_CHANNELS.CEO_LOAD_AGENTS, projectPath),

  getAgent: (projectPath: string, agentName: string): Promise<IPCResult<AgentDefinition | null>> =>
    invokeIpc(IPC_CHANNELS.CEO_GET_AGENT, projectPath, agentName),

  getTeams: (projectPath: string): Promise<IPCResult<Record<string, TeamInfo>>> =>
    invokeIpc(IPC_CHANNELS.CEO_GET_TEAMS, projectPath),

  classifyTask: (projectPath: string, request: string): Promise<IPCResult<RoutingResult>> =>
    invokeIpc(IPC_CHANNELS.CEO_CLASSIFY_TASK, projectPath, request),

  routeTask: (projectPath: string, request: string): Promise<IPCResult<RoutingResult>> =>
    invokeIpc(IPC_CHANNELS.CEO_ROUTE_TASK, projectPath, request)
});
