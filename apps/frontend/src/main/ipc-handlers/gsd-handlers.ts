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

  /**
   * Get SharedBoard for CEO Team Kanban
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_GET_SHARED_BOARD,
    async (_event: IpcMainInvokeEvent, projectPath: string, phase?: number): Promise<IPCResult> => {
      try {
        logger.info('gsd:getSharedBoard', { projectPath, phase });
        const gsdService = getGsdService(projectPath);
        const board = await gsdService.getSharedBoard(phase);
        return { success: true, data: board };
      } catch (error) {
        logger.error('gsd:getSharedBoard failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Get LeaderContext for CEO Dashboard
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_GET_LEADER_CONTEXT,
    async (_event: IpcMainInvokeEvent, projectPath: string, phase?: number): Promise<IPCResult> => {
      try {
        logger.info('gsd:getLeaderContext', { projectPath, phase });
        const gsdService = getGsdService(projectPath);
        const context = await gsdService.getLeaderContext(phase);
        return { success: true, data: context };
      } catch (error) {
        logger.error('gsd:getLeaderContext failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Get pending verifications for manual UAT
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_GET_PENDING_VERIFICATIONS,
    async (_event: IpcMainInvokeEvent, projectPath: string): Promise<IPCResult> => {
      try {
        logger.info('gsd:getPendingVerifications', { projectPath });
        const gsdService = getGsdService(projectPath);
        const verifications = await gsdService.getPendingVerifications();
        return { success: true, data: verifications };
      } catch (error) {
        logger.error('gsd:getPendingVerifications failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Submit verification result (approve/reject)
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_SUBMIT_VERIFICATION,
    async (
      _event: IpcMainInvokeEvent,
      projectPath: string,
      planId: string,
      approved: boolean,
      feedback?: string,
      checklist?: Array<{ id: string; description: string; checked: boolean }>
    ): Promise<IPCResult> => {
      try {
        logger.info('gsd:submitVerification', { projectPath, planId, approved });
        const gsdService = getGsdService(projectPath);
        const result = await gsdService.submitVerification(planId, approved, feedback, checklist);
        return { success: result.success, error: result.error };
      } catch (error) {
        logger.error('gsd:submitVerification failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Create a new GSD project
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_CREATE_PROJECT,
    async (
      _event: IpcMainInvokeEvent,
      projectPath: string,
      input: { name: string; description: string; coreValue?: string }
    ): Promise<IPCResult> => {
      try {
        logger.info('gsd:createProject', { projectPath, name: input.name });
        const gsdService = getGsdService(projectPath);
        const result = await gsdService.createProject(input);
        return { success: result.success, data: result, error: result.error };
      } catch (error) {
        logger.error('gsd:createProject failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  logger.info('[GSD] IPC handlers registered');
}
