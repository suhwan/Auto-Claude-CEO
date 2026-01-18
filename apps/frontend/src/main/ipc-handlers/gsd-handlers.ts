/**
 * GSD (Get Shit Done) IPC Handlers
 *
 * GSD workflow and kanban sync IPC handlers
 */

import { ipcMain, IpcMainInvokeEvent } from 'electron';
import { IPC_CHANNELS } from '../../shared/constants';
import type { IPCResult } from '../../shared/types/common';
import { GsdService } from '../gsd-service';
import { logger } from '../app-logger';

// Project-based GSD Service instance cache
const gsdServiceCache = new Map<string, GsdService>();

/**
 * Get GSD Service instance (with caching)
 */
function getGsdService(projectPath: string): GsdService {
  if (!gsdServiceCache.has(projectPath)) {
    gsdServiceCache.set(projectPath, new GsdService(projectPath));
  }
  return gsdServiceCache.get(projectPath)!;
}

export function setupGsdHandlers(): void {
  /**
   * Get ROADMAP.md data
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_GET_ROADMAP,
    async (_event: IpcMainInvokeEvent, projectPath: string, roadmapPath?: string): Promise<IPCResult> => {
      try {
        logger.info('gsd:getRoadmap', { projectPath, roadmapPath });
        const gsdService = getGsdService(projectPath);
        const roadmap = await gsdService.getRoadmap(roadmapPath);
        return { success: true, data: roadmap };
      } catch (error) {
        logger.error('gsd:getRoadmap failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Get STATE.md data
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_GET_STATE,
    async (_event: IpcMainInvokeEvent, projectPath: string, statePath?: string): Promise<IPCResult> => {
      try {
        logger.info('gsd:getState', { projectPath, statePath });
        const gsdService = getGsdService(projectPath);
        const state = await gsdService.getState(statePath);
        return { success: true, data: state };
      } catch (error) {
        logger.error('gsd:getState failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Get detailed plan information
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_GET_PLAN_DETAIL,
    async (_event: IpcMainInvokeEvent, projectPath: string, planPath: string): Promise<IPCResult> => {
      try {
        logger.info('gsd:getPlanDetail', { projectPath, planPath });
        const gsdService = getGsdService(projectPath);
        const detail = await gsdService.getPlanDetail(planPath);
        return { success: true, data: detail };
      } catch (error) {
        logger.error('gsd:getPlanDetail failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Sync PLAN.md to kanban
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_SYNC_PLAN_TO_KANBAN,
    async (_event: IpcMainInvokeEvent, projectPath: string, planPath: string): Promise<IPCResult> => {
      try {
        logger.info('gsd:syncPlanToKanban', { projectPath, planPath });
        const gsdService = getGsdService(projectPath);
        const result = await gsdService.syncPlanToKanban(planPath);
        return { success: true, data: result };
      } catch (error) {
        logger.error('gsd:syncPlanToKanban failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Sync entire phase to kanban
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_SYNC_PHASE_TO_KANBAN,
    async (_event: IpcMainInvokeEvent, projectPath: string, phaseNumber: number): Promise<IPCResult> => {
      try {
        logger.info('gsd:syncPhaseToKanban', { projectPath, phaseNumber });
        const gsdService = getGsdService(projectPath);
        const result = await gsdService.syncPhaseToKanban(phaseNumber);
        return { success: true, data: result };
      } catch (error) {
        logger.error('gsd:syncPhaseToKanban failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Get phase progress
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_GET_PHASE_PROGRESS,
    async (_event: IpcMainInvokeEvent, projectPath: string, roadmapPath?: string): Promise<IPCResult> => {
      try {
        logger.info('gsd:getPhaseProgress', { projectPath, roadmapPath });
        const gsdService = getGsdService(projectPath);
        const progress = await gsdService.getPhaseProgress(roadmapPath);
        return { success: true, data: progress };
      } catch (error) {
        logger.error('gsd:getPhaseProgress failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Update task status
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_UPDATE_TASK_STATUS,
    async (_event: IpcMainInvokeEvent, projectPath: string, taskId: string, status: string): Promise<IPCResult> => {
      try {
        logger.info('gsd:updateTaskStatus', { projectPath, taskId, status });
        const gsdService = getGsdService(projectPath);
        const success = await gsdService.updateTaskStatus(taskId, status);
        return { success: true, data: { success } };
      } catch (error) {
        logger.error('gsd:updateTaskStatus failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Generate SUMMARY.md
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_GENERATE_SUMMARY,
    async (_event: IpcMainInvokeEvent, projectPath: string, planPath: string): Promise<IPCResult> => {
      try {
        logger.info('gsd:generateSummary', { projectPath, planPath });
        const gsdService = getGsdService(projectPath);
        const summaryPath = await gsdService.generateSummary(planPath);
        return { success: true, data: { summaryPath } };
      } catch (error) {
        logger.error('gsd:generateSummary failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Get sync status
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_GET_SYNC_STATUS,
    async (_event: IpcMainInvokeEvent, projectPath: string): Promise<IPCResult> => {
      try {
        logger.info('gsd:getSyncStatus', { projectPath });
        const gsdService = getGsdService(projectPath);
        const status = await gsdService.getSyncStatus();
        return { success: true, data: status };
      } catch (error) {
        logger.error('gsd:getSyncStatus failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  logger.info('[GSD] IPC handlers registered');
}
