/**
 * GSD Parallel Executor
 *
 * Manages parallel execution of multiple GSD plans within a phase.
 * Uses dependency analysis to determine execution waves and runs
 * multiple Claude CLI processes simultaneously.
 */

import { EventEmitter } from 'events';
import { spawn, ChildProcess, execSync } from 'child_process';
import * as path from 'path';
import { GsdDependencyAnalyzer, ExecutionPhase, ExecutionWave } from './gsd-dependency-analyzer';
import { logger } from './app-logger';

export interface TaskProgress {
  taskId: string;
  planId: string;
  sessionId: string;
  status: 'pending' | 'ready' | 'running' | 'complete' | 'error';
  progress?: number;
  output?: string;
  error?: string;
}

export interface TaskExecutionResult {
  taskId: string;
  planId: string;
  success: boolean;
  output: string;
  error?: string;
  duration: number; // milliseconds
}

export interface PhaseExecutionResult {
  phaseNumber: number;
  totalTasks: number;
  successful: number;
  failed: number;
  duration: number; // milliseconds
  results: TaskExecutionResult[];
}

interface ExecutionSession {
  sessionId: string;
  taskId: string;
  planId: string;
  process: ChildProcess | null;
  status: 'running' | 'complete' | 'error';
  output: string;
  startedAt: Date;
}

// Singleton instance for managing parallel executions
let instance: GsdParallelExecutor | null = null;

export class GsdParallelExecutor extends EventEmitter {
  private sessions: Map<string, ExecutionSession> = new Map();
  private maxParallel: number = 3; // Maximum concurrent executions
  private projectPath: string;
  private cancelled: boolean = false;

  constructor(projectPath: string) {
    super();
    this.projectPath = projectPath;
  }

  static getInstance(projectPath?: string): GsdParallelExecutor {
    if (!instance && projectPath) {
      instance = new GsdParallelExecutor(projectPath);
    }
    return instance!;
  }

  static resetInstance(): void {
    if (instance) {
      instance.cancelAll();
      instance = null;
    }
  }

  /**
   * Execute all plans in a phase with parallel execution where possible
   */
  async executePhaseParallel(
    phaseNumber: number,
    onProgress: (updates: TaskProgress[]) => void
  ): Promise<PhaseExecutionResult> {
    this.cancelled = false;
    const startTime = Date.now();

    const analyzer = new GsdDependencyAnalyzer(this.projectPath);
    const phase = await analyzer.getPhaseExecutionPlan(phaseNumber);

    if (!phase) {
      throw new Error(`Phase ${phaseNumber} not found`);
    }

    logger.info('[ParallelExecutor] Starting phase execution', {
      phaseNumber,
      totalTasks: phase.totalTasks,
      parallelizable: phase.parallelizable,
      waves: phase.waves.length
    });

    const results: TaskExecutionResult[] = [];

    // Execute waves sequentially (waves can contain parallel tasks)
    for (const wave of phase.waves) {
      if (this.cancelled) {
        logger.info('[ParallelExecutor] Execution cancelled');
        break;
      }

      logger.info('[ParallelExecutor] Starting wave', {
        waveNumber: wave.waveNumber,
        tasks: wave.tasks,
        isParallel: wave.isParallel
      });

      const waveResults = await this.executeWave(wave, onProgress);
      results.push(...waveResults);

      // Stop if any task failed
      const failedTasks = waveResults.filter(r => !r.success);
      if (failedTasks.length > 0) {
        logger.warn('[ParallelExecutor] Wave had failures, stopping', {
          failedTasks: failedTasks.map(t => t.taskId)
        });
        break;
      }
    }

    const duration = Date.now() - startTime;

    return {
      phaseNumber,
      totalTasks: results.length,
      successful: results.filter(r => r.success).length,
      failed: results.filter(r => !r.success).length,
      duration,
      results
    };
  }

  /**
   * Execute tasks within a wave (with parallelization if applicable)
   */
  private async executeWave(
    wave: ExecutionWave,
    onProgress: (updates: TaskProgress[]) => void
  ): Promise<TaskExecutionResult[]> {
    // Chunk tasks by maxParallel limit
    const chunks = this.chunkArray(wave.tasks, this.maxParallel);
    const results: TaskExecutionResult[] = [];

    for (const chunk of chunks) {
      if (this.cancelled) break;

      // Execute chunk in parallel
      const chunkResults = await Promise.all(
        chunk.map(taskId => this.executeTask(taskId, onProgress))
      );
      results.push(...chunkResults);
    }

    return results;
  }

  /**
   * Execute a single task (GSD plan)
   */
  private async executeTask(
    taskId: string,
    onProgress: (updates: TaskProgress[]) => void
  ): Promise<TaskExecutionResult> {
    const startTime = Date.now();
    const sessionId = `${taskId}-${Date.now()}`;
    const planId = taskId.replace('gsd-', '');

    // Find the plan path
    const planPath = await this.findPlanPath(planId);

    if (!planPath) {
      return {
        taskId,
        planId,
        success: false,
        output: '',
        error: `Plan file not found for ${planId}`,
        duration: Date.now() - startTime
      };
    }

    const session: ExecutionSession = {
      sessionId,
      taskId,
      planId,
      process: null,
      status: 'running',
      output: '',
      startedAt: new Date()
    };

    this.sessions.set(sessionId, session);

    // Emit initial progress
    onProgress([{
      taskId,
      planId,
      sessionId,
      status: 'running',
      progress: 0,
      output: ''
    }]);

    return new Promise((resolve) => {
      this.runClaudeExecution(session, planPath, (chunk) => {
        session.output += chunk;
        onProgress([{
          taskId,
          planId,
          sessionId,
          status: 'running',
          output: chunk,
          progress: this.parseProgress(session.output)
        }]);
      }, (success, error) => {
        session.status = success ? 'complete' : 'error';
        const duration = Date.now() - startTime;

        onProgress([{
          taskId,
          planId,
          sessionId,
          status: success ? 'complete' : 'error',
          progress: success ? 100 : undefined,
          error
        }]);

        resolve({
          taskId,
          planId,
          success,
          output: session.output,
          error,
          duration
        });
      });
    });
  }

  /**
   * Run Claude CLI to execute a plan
   */
  private async runClaudeExecution(
    session: ExecutionSession,
    planPath: string,
    onOutput: (chunk: string) => void,
    onComplete: (success: boolean, error?: string) => void
  ): Promise<void> {
    const claudePath = await this.findClaudePath();

    if (!claudePath) {
      onComplete(false, 'Claude Code CLI not found. Please install it first.');
      return;
    }

    // Escape the plan path for shell
    const escapedPath = planPath.replace(/"/g, '\\"');

    logger.info('[ParallelExecutor] Starting task execution', {
      sessionId: session.sessionId,
      taskId: session.taskId,
      planPath
    });

    session.process = spawn(claudePath, [
      '--print', `/gsd:execute-plan "${escapedPath}"`,
      '--allowedTools', 'Read,Write,Edit,Glob,Grep,Bash,Task',
      '--max-turns', '50'
    ], {
      cwd: this.projectPath,
      env: { ...process.env },
      shell: true
    });

    session.process.stdout?.on('data', (data: Buffer) => {
      const output = data.toString();
      onOutput(output);
    });

    session.process.stderr?.on('data', (data: Buffer) => {
      const text = data.toString();
      onOutput(text);
    });

    session.process.on('close', (code: number | null) => {
      logger.info('[ParallelExecutor] Task completed', {
        sessionId: session.sessionId,
        code
      });
      onComplete(code === 0);
    });

    session.process.on('error', (err: Error) => {
      logger.error('[ParallelExecutor] Task error:', err);
      onComplete(false, err.message);
    });
  }

  /**
   * Find the PLAN.md file path for a given plan ID
   */
  private async findPlanPath(planId: string): Promise<string | null> {
    const fs = await import('fs');
    const phasesDir = path.join(this.projectPath, '.planning', 'phases');

    if (!fs.existsSync(phasesDir)) {
      return null;
    }

    // List phase directories
    const dirs = fs.readdirSync(phasesDir);

    // Find matching plan file
    for (const dir of dirs) {
      const dirPath = path.join(phasesDir, dir);
      const stat = fs.statSync(dirPath);

      if (stat.isDirectory()) {
        const planFile = `${planId}-PLAN.md`;
        const planFilePath = path.join(dirPath, planFile);

        if (fs.existsSync(planFilePath)) {
          return planFilePath;
        }
      }
    }

    return null;
  }

  /**
   * Parse progress percentage from output
   */
  private parseProgress(output: string): number {
    // Look for [X/Y] pattern
    const matches = output.match(/\[(\d+)\/(\d+)\]/g);
    if (matches && matches.length > 0) {
      const lastMatch = matches[matches.length - 1];
      const [, current, total] = lastMatch.match(/\[(\d+)\/(\d+)\]/) || [];
      if (current && total) {
        return Math.round((parseInt(current, 10) / parseInt(total, 10)) * 100);
      }
    }

    // Look for percentage
    const percentMatch = output.match(/(\d+)%/g);
    if (percentMatch && percentMatch.length > 0) {
      const lastPercent = percentMatch[percentMatch.length - 1];
      return parseInt(lastPercent, 10);
    }

    return 0;
  }

  /**
   * Find Claude CLI path
   */
  private async findClaudePath(): Promise<string | null> {
    try {
      const cmd = process.platform === 'win32' ? 'where claude' : 'which claude';
      const result = execSync(cmd, { encoding: 'utf-8' }).trim().split('\n')[0];
      return result;
    } catch {
      // Try common paths
      const commonPaths = process.platform === 'win32'
        ? ['C:\\Program Files\\Claude\\claude.exe', '%LOCALAPPDATA%\\Programs\\Claude\\claude.exe']
        : ['/usr/local/bin/claude', '/opt/homebrew/bin/claude'];

      for (const p of commonPaths) {
        try {
          const fs = await import('fs');
          const expandedPath = p.replace(/%([^%]+)%/g, (_, key) => process.env[key] || '');
          if (fs.existsSync(expandedPath)) {
            return expandedPath;
          }
        } catch {
          continue;
        }
      }
      return null;
    }
  }

  /**
   * Split array into chunks
   */
  private chunkArray<T>(arr: T[], size: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < arr.length; i += size) {
      chunks.push(arr.slice(i, i + size));
    }
    return chunks;
  }

  /**
   * Cancel all running executions
   */
  cancelAll(): void {
    this.cancelled = true;
    logger.info('[ParallelExecutor] Cancelling all executions');

    for (const session of this.sessions.values()) {
      if (session.status === 'running' && session.process) {
        session.process.kill();
      }
    }
    this.sessions.clear();
  }

  /**
   * Get active session count
   */
  getActiveCount(): number {
    return Array.from(this.sessions.values())
      .filter(s => s.status === 'running')
      .length;
  }

  /**
   * Set maximum parallel executions
   */
  setMaxParallel(max: number): void {
    this.maxParallel = Math.max(1, Math.min(max, 5)); // Limit 1-5
  }
}

export default GsdParallelExecutor;
