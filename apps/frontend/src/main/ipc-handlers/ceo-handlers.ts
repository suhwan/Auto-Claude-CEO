/**
 * CEO IPC Handlers
 *
 * CEO agent and routing IPC handlers
 */

import { ipcMain, IpcMainInvokeEvent } from 'electron';
import { IPC_CHANNELS } from '../../shared/constants';
import type { IPCResult } from '../../shared/types/common';
import { CeoService } from '../ceo-service';
import { logger } from '../app-logger';

// Project-based CEO Service instance cache
const ceoServiceCache = new Map<string, CeoService>();

/**
 * Get CEO Service instance (with caching)
 */
function getCeoService(projectPath: string): CeoService {
  if (!ceoServiceCache.has(projectPath)) {
    ceoServiceCache.set(projectPath, new CeoService(projectPath));
  }
  return ceoServiceCache.get(projectPath)!;
}

export function setupCeoHandlers(): void {
  /**
   * Load all agents from project
   */
  ipcMain.handle(
    IPC_CHANNELS.CEO_LOAD_AGENTS,
    async (_event: IpcMainInvokeEvent, projectPath: string): Promise<IPCResult> => {
      try {
        logger.info('ceo:loadAgents', { projectPath });
        const ceoService = getCeoService(projectPath);
        const data = await ceoService.loadAgents();
        return { success: true, data };
      } catch (error) {
        logger.error('ceo:loadAgents failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Get specific agent by name
   */
  ipcMain.handle(
    IPC_CHANNELS.CEO_GET_AGENT,
    async (_event: IpcMainInvokeEvent, projectPath: string, agentName: string): Promise<IPCResult> => {
      try {
        logger.info('ceo:getAgent', { projectPath, agentName });
        const ceoService = getCeoService(projectPath);
        const agent = ceoService.getAgent(agentName);
        return { success: true, data: agent };
      } catch (error) {
        logger.error('ceo:getAgent failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Get all teams
   */
  ipcMain.handle(
    IPC_CHANNELS.CEO_GET_TEAMS,
    async (_event: IpcMainInvokeEvent, projectPath: string): Promise<IPCResult> => {
      try {
        logger.info('ceo:getTeams', { projectPath });
        const ceoService = getCeoService(projectPath);
        const teams = ceoService.getTeams();
        return { success: true, data: teams };
      } catch (error) {
        logger.error('ceo:getTeams failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Classify task as coding/non-coding
   */
  ipcMain.handle(
    IPC_CHANNELS.CEO_CLASSIFY_TASK,
    async (_event: IpcMainInvokeEvent, projectPath: string, request: string): Promise<IPCResult> => {
      try {
        logger.info('ceo:classifyTask', { projectPath, request: request.substring(0, 100) });
        const ceoService = getCeoService(projectPath);
        const result = ceoService.classifyTask(request);
        return { success: true, data: result };
      } catch (error) {
        logger.error('ceo:classifyTask failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Route task to appropriate team/system
   */
  ipcMain.handle(
    IPC_CHANNELS.CEO_ROUTE_TASK,
    async (_event: IpcMainInvokeEvent, projectPath: string, request: string): Promise<IPCResult> => {
      try {
        logger.info('ceo:routeTask', { projectPath, request: request.substring(0, 100) });
        const ceoService = getCeoService(projectPath);
        const result = ceoService.routeTask(request);
        return { success: true, data: result };
      } catch (error) {
        logger.error('ceo:routeTask failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  logger.info('[CEO] IPC handlers registered');
}
