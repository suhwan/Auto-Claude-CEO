/**
 * GSD (Get Shit Done) IPC Handlers
 *
 * GSD workflow and kanban sync IPC handlers
 */

import { ipcMain, IpcMainInvokeEvent, BrowserWindow } from 'electron';
import { IPC_CHANNELS } from '../../shared/constants';
import type { IPCResult } from '../../shared/types/common';
import { GsdService, RoadmapGenerator, PlanGenerator, ChatGenerator, GenerateRoadmapInput, PlanPhaseInput, ResearchPhaseInput, ExecutePlanInput, GsdChatInput } from '../gsd-service';
import { GsdDependencyAnalyzer } from '../gsd-dependency-analyzer';
import { GsdParallelExecutor, TaskProgress, PhaseExecutionResult } from '../gsd-parallel-executor';
import { logger } from '../app-logger';

// Project-based GSD Service instance cache
const gsdServiceCache = new Map<string, GsdService>();

// Store active roadmap generators
const activeGenerators = new Map<string, RoadmapGenerator>();

// Store active plan generators
const activePlanGenerators = new Map<string, PlanGenerator>();

// Store active chat generators
const activeChatGenerators = new Map<string, ChatGenerator>();

// Store active parallel executor (one per project)
let activeParallelExecutor: GsdParallelExecutor | null = null;

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

  /**
   * Generate roadmap using Claude Code CLI
   * Returns generatorId for tracking streaming output
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_GENERATE_ROADMAP,
    async (
      event: IpcMainInvokeEvent,
      projectPath: string,
      input: GenerateRoadmapInput
    ): Promise<IPCResult<{ generatorId: string }>> => {
      try {
        logger.info('gsd:generateRoadmap', { projectPath, depth: input.depth });

        const gsdService = getGsdService(projectPath);
        const generator = gsdService.createRoadmapGenerator();
        const generatorId = `gen-${Date.now()}`;

        activeGenerators.set(generatorId, generator);

        // Get the sender window
        const window = BrowserWindow.fromWebContents(event.sender);

        // Setup event forwarding
        generator.on('output', (data: string) => {
          window?.webContents.send('gsd:roadmap-output', { generatorId, data });
        });

        generator.on('error', (error: string) => {
          window?.webContents.send('gsd:roadmap-error', { generatorId, error });
        });

        generator.on('complete', (success: boolean) => {
          window?.webContents.send('gsd:roadmap-complete', { generatorId, success });
          activeGenerators.delete(generatorId);
        });

        // Start generation (don't await - it runs asynchronously)
        generator.generate(input);

        return { success: true, data: { generatorId } };
      } catch (error) {
        logger.error('gsd:generateRoadmap failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Cancel roadmap generation
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_CANCEL_GENERATION,
    async (_event: IpcMainInvokeEvent, generatorId: string): Promise<IPCResult<void>> => {
      try {
        logger.info('gsd:cancelGeneration', { generatorId });
        const generator = activeGenerators.get(generatorId);
        if (generator) {
          generator.cancel();
          activeGenerators.delete(generatorId);
        }
        return { success: true };
      } catch (error) {
        logger.error('gsd:cancelGeneration failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Plan a phase using Claude Code CLI
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_PLAN_PHASE,
    async (
      event: IpcMainInvokeEvent,
      projectPath: string,
      input: PlanPhaseInput
    ): Promise<IPCResult<{ generatorId: string }>> => {
      try {
        logger.info('gsd:planPhase', { projectPath, phase: input.phaseNumber });

        const gsdService = getGsdService(projectPath);
        const generator = gsdService.createPlanGenerator();
        const generatorId = `plan-${Date.now()}`;

        activePlanGenerators.set(generatorId, generator);

        const window = BrowserWindow.fromWebContents(event.sender);

        generator.on('output', (data: string) => {
          window?.webContents.send('gsd:plan-output', { generatorId, data });
        });

        generator.on('progress', (progress: { current: number; total: number }) => {
          window?.webContents.send('gsd:plan-progress', { generatorId, ...progress });
        });

        generator.on('error', (error: string) => {
          window?.webContents.send('gsd:plan-error', { generatorId, error });
        });

        generator.on('complete', (success: boolean) => {
          window?.webContents.send('gsd:plan-complete', { generatorId, success });
          activePlanGenerators.delete(generatorId);
        });

        generator.planPhase(input);

        return { success: true, data: { generatorId } };
      } catch (error) {
        logger.error('gsd:planPhase failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Research a phase using Claude Code CLI
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_RESEARCH_PHASE,
    async (
      event: IpcMainInvokeEvent,
      projectPath: string,
      input: ResearchPhaseInput
    ): Promise<IPCResult<{ generatorId: string }>> => {
      try {
        logger.info('gsd:researchPhase', { projectPath, phase: input.phaseNumber });

        const gsdService = getGsdService(projectPath);
        const generator = gsdService.createPlanGenerator();
        const generatorId = `research-${Date.now()}`;

        activePlanGenerators.set(generatorId, generator);

        const window = BrowserWindow.fromWebContents(event.sender);

        generator.on('output', (data: string) => {
          window?.webContents.send('gsd:research-output', { generatorId, data });
        });

        generator.on('progress', (progress: { current: number; total: number }) => {
          window?.webContents.send('gsd:research-progress', { generatorId, ...progress });
        });

        generator.on('error', (error: string) => {
          window?.webContents.send('gsd:research-error', { generatorId, error });
        });

        generator.on('complete', (success: boolean) => {
          window?.webContents.send('gsd:research-complete', { generatorId, success });
          activePlanGenerators.delete(generatorId);
        });

        generator.researchPhase(input);

        return { success: true, data: { generatorId } };
      } catch (error) {
        logger.error('gsd:researchPhase failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Execute a plan using Claude Code CLI
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_EXECUTE_PLAN,
    async (
      event: IpcMainInvokeEvent,
      projectPath: string,
      input: ExecutePlanInput
    ): Promise<IPCResult<{ generatorId: string }>> => {
      try {
        logger.info('gsd:executePlan', { projectPath, planPath: input.planPath });

        const gsdService = getGsdService(projectPath);
        const generator = gsdService.createPlanGenerator();
        const generatorId = `exec-${Date.now()}`;

        activePlanGenerators.set(generatorId, generator);

        const window = BrowserWindow.fromWebContents(event.sender);

        generator.on('output', (data: string) => {
          window?.webContents.send('gsd:execute-output', { generatorId, data });
        });

        generator.on('progress', (progress: { current: number; total: number }) => {
          window?.webContents.send('gsd:execute-progress', { generatorId, ...progress });
        });

        generator.on('error', (error: string) => {
          window?.webContents.send('gsd:execute-error', { generatorId, error });
        });

        generator.on('complete', (success: boolean) => {
          window?.webContents.send('gsd:execute-complete', { generatorId, success });
          activePlanGenerators.delete(generatorId);
        });

        generator.executePlan(input);

        return { success: true, data: { generatorId } };
      } catch (error) {
        logger.error('gsd:executePlan failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Cancel plan generation or execution
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_CANCEL_PLAN,
    async (_event: IpcMainInvokeEvent, generatorId: string): Promise<IPCResult<void>> => {
      try {
        logger.info('gsd:cancelPlan', { generatorId });
        const generator = activePlanGenerators.get(generatorId);
        if (generator) {
          generator.cancel();
          activePlanGenerators.delete(generatorId);
        }
        return { success: true };
      } catch (error) {
        logger.error('gsd:cancelPlan failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Start a GSD chat session for project creation
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_START_CHAT_SESSION,
    async (
      event: IpcMainInvokeEvent,
      projectPath: string,
      idea: GsdChatInput
    ): Promise<IPCResult<{ sessionId: string }>> => {
      try {
        logger.info('gsd:startChatSession', { projectPath, title: idea.title });

        const gsdService = getGsdService(projectPath);
        const generator = gsdService.createChatGenerator();
        const sessionId = generator.getSessionId();

        activeChatGenerators.set(sessionId, generator);

        const window = BrowserWindow.fromWebContents(event.sender);

        // Setup event forwarding
        generator.on('message', (data: string) => {
          window?.webContents.send('gsd:chat:message', data);
        });

        generator.on('error', (error: string) => {
          window?.webContents.send('gsd:chat:error', error);
          activeChatGenerators.delete(sessionId);
        });

        generator.on('complete', (result: { gsdPath: string }) => {
          window?.webContents.send('gsd:chat:complete', result);
          activeChatGenerators.delete(sessionId);
        });

        // Start the chat session
        generator.start(idea);

        return { success: true, data: { sessionId } };
      } catch (error) {
        logger.error('gsd:startChatSession failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Send a message to an active chat session
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_SEND_CHAT_MESSAGE,
    async (
      _event: IpcMainInvokeEvent,
      sessionId: string,
      message: string
    ): Promise<IPCResult<void>> => {
      try {
        logger.info('gsd:sendChatMessage', { sessionId, messageLength: message.length });

        const generator = activeChatGenerators.get(sessionId);
        if (!generator) {
          return { success: false, error: 'Chat session not found' };
        }

        generator.sendMessage(message);
        return { success: true };
      } catch (error) {
        logger.error('gsd:sendChatMessage failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * End a chat session
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_END_CHAT_SESSION,
    async (_event: IpcMainInvokeEvent, sessionId: string): Promise<IPCResult<void>> => {
      try {
        logger.info('gsd:endChatSession', { sessionId });

        const generator = activeChatGenerators.get(sessionId);
        if (generator) {
          generator.end();
          activeChatGenerators.delete(sessionId);
        }

        return { success: true };
      } catch (error) {
        logger.error('gsd:endChatSession failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Get GSD tasks for Kanban display
   * Converts ROADMAP.md phases/plans into Kanban-compatible task structures
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_GET_KANBAN_TASKS,
    async (_event: IpcMainInvokeEvent, projectPath: string, roadmapPath?: string): Promise<IPCResult> => {
      try {
        logger.info('gsd:getKanbanTasks', { projectPath, roadmapPath });
        const gsdService = getGsdService(projectPath);
        const result = await gsdService.convertRoadmapToTasks(roadmapPath);
        return { success: true, data: result };
      } catch (error) {
        logger.error('gsd:getKanbanTasks failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Sync GSD plans to Kanban board
   * Creates/updates tasks in .auto-claude/specs from ROADMAP phases
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_SYNC_TO_KANBAN,
    async (_event: IpcMainInvokeEvent, projectPath: string): Promise<IPCResult> => {
      try {
        logger.info('gsd:syncToKanban', { projectPath });
        const gsdService = getGsdService(projectPath);

        // Get roadmap info to iterate through phases
        const roadmap = await gsdService.getRoadmap();
        let totalSynced = 0;
        const syncResults: Array<{ phaseNumber: number; taskCount: number }> = [];

        // Sync each phase to kanban
        for (const phase of roadmap.phases) {
          const result = await gsdService.syncPhaseToKanban(phase.number);
          if (result.success && result.task_count) {
            totalSynced += result.task_count;
            syncResults.push({
              phaseNumber: phase.number,
              taskCount: result.task_count
            });
          }
        }

        return {
          success: true,
          data: {
            totalSynced,
            phases: syncResults
          }
        };
      } catch (error) {
        logger.error('gsd:syncToKanban failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Get execution plan for a phase
   * Analyzes dependencies and returns wave-based execution plan
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_GET_EXECUTION_PLAN,
    async (_event: IpcMainInvokeEvent, projectPath: string, phaseNumber: number): Promise<IPCResult> => {
      try {
        logger.info('gsd:getExecutionPlan', { projectPath, phaseNumber });
        const analyzer = new GsdDependencyAnalyzer(projectPath);
        const phasePlan = await analyzer.getPhaseExecutionPlan(phaseNumber);
        return { success: true, data: phasePlan };
      } catch (error) {
        logger.error('gsd:getExecutionPlan failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Execute all plans in a phase with parallel execution
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_EXECUTE_PHASE_PARALLEL,
    async (event: IpcMainInvokeEvent, projectPath: string, phaseNumber: number): Promise<IPCResult> => {
      try {
        logger.info('gsd:executePhaseParallel', { projectPath, phaseNumber });

        // Cancel any existing executor
        if (activeParallelExecutor) {
          activeParallelExecutor.cancelAll();
        }

        // Create new executor
        activeParallelExecutor = new GsdParallelExecutor(projectPath);
        const window = BrowserWindow.fromWebContents(event.sender);

        // Execute with progress callbacks
        const result = await activeParallelExecutor.executePhaseParallel(
          phaseNumber,
          (updates: TaskProgress[]) => {
            window?.webContents.send('gsd:parallel:progress', updates);
          }
        );

        // Send completion event
        window?.webContents.send('gsd:parallel:complete', result);

        activeParallelExecutor = null;
        return { success: true, data: result };
      } catch (error) {
        logger.error('gsd:executePhaseParallel failed:', error);
        activeParallelExecutor = null;
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  /**
   * Cancel ongoing parallel execution
   */
  ipcMain.handle(
    IPC_CHANNELS.GSD_CANCEL_PARALLEL_EXECUTION,
    async (): Promise<IPCResult<void>> => {
      try {
        logger.info('gsd:cancelParallelExecution');
        if (activeParallelExecutor) {
          activeParallelExecutor.cancelAll();
          activeParallelExecutor = null;
        }
        return { success: true };
      } catch (error) {
        logger.error('gsd:cancelParallelExecution failed:', error);
        return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
      }
    }
  );

  logger.info('[GSD] IPC handlers registered');
}
