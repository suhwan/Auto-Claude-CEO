/**
 * GSD Dependency Analyzer
 *
 * Analyzes PLAN.md frontmatter for parallel_safe and depends_on fields
 * to build an execution plan with waves of parallelizable tasks.
 */

import * as path from 'path';
import { GsdService } from './gsd-service';
import type { GsdConvertedTask } from './gsd-service';

export interface TaskNode {
  id: string;           // Plan ID (e.g., "gsd-03-01")
  planId: string;       // Raw plan ID (e.g., "03-01")
  parallelSafe: boolean;
  dependsOn: string[];
  status: 'pending' | 'ready' | 'running' | 'complete' | 'blocked';
  blockedBy?: string[]; // Dependencies not yet completed
  phaseNumber: number;
  planNumber: number;
  title: string;
}

export interface ExecutionWave {
  waveNumber: number;
  tasks: string[];         // Task IDs that can run in parallel
  isParallel: boolean;     // True if multiple tasks in wave
}

export interface ExecutionPhase {
  phaseNumber: number;
  phaseName: string;
  waves: ExecutionWave[];
  totalTasks: number;
  parallelizable: number;
}

export interface ExecutionPlan {
  phases: ExecutionPhase[];
  totalTasks: number;
  parallelizable: number;
}

export class GsdDependencyAnalyzer {
  private projectPath: string;
  private gsdService: GsdService;

  constructor(projectPath: string) {
    this.projectPath = projectPath;
    this.gsdService = new GsdService(projectPath);
  }

  /**
   * Load all task nodes from ROADMAP.md
   */
  async loadTaskNodes(): Promise<TaskNode[]> {
    const result = await this.gsdService.convertRoadmapToTasks();

    return result.tasks.map(task => ({
      id: task.id,
      planId: task.id.replace('gsd-', ''),
      parallelSafe: task.parallelSafe,
      dependsOn: task.dependsOn,
      status: task.status === 'complete' ? 'complete' : 'pending',
      phaseNumber: task.phaseNumber,
      planNumber: task.planNumber,
      title: task.title
    }));
  }

  /**
   * Generate execution plan from ROADMAP.md
   */
  async analyzeExecutionPlan(): Promise<ExecutionPlan> {
    const tasks = await this.loadTaskNodes();
    const phases = this.groupByPhase(tasks);
    const result = await this.gsdService.convertRoadmapToTasks();

    const executionPhases: ExecutionPhase[] = [];
    let totalParallelizable = 0;

    for (const phase of phases) {
      const waves = this.calculateWaves(phase.tasks);
      const phaseInfo = result.phases.find(p => p.phaseNumber === phase.number);
      const parallelizable = phase.tasks.filter(t => t.parallelSafe).length;
      totalParallelizable += parallelizable;

      executionPhases.push({
        phaseNumber: phase.number,
        phaseName: phaseInfo?.name || `Phase ${phase.number}`,
        waves,
        totalTasks: phase.tasks.length,
        parallelizable
      });
    }

    return {
      phases: executionPhases,
      totalTasks: tasks.length,
      parallelizable: totalParallelizable
    };
  }

  /**
   * Get execution plan for a specific phase
   */
  async getPhaseExecutionPlan(phaseNumber: number): Promise<ExecutionPhase | null> {
    const plan = await this.analyzeExecutionPlan();
    return plan.phases.find(p => p.phaseNumber === phaseNumber) || null;
  }

  /**
   * Group tasks by phase number
   */
  private groupByPhase(tasks: TaskNode[]): { number: number; tasks: TaskNode[] }[] {
    const phaseMap = new Map<number, TaskNode[]>();

    for (const task of tasks) {
      const existing = phaseMap.get(task.phaseNumber) || [];
      existing.push(task);
      phaseMap.set(task.phaseNumber, existing);
    }

    return Array.from(phaseMap.entries())
      .map(([number, tasks]) => ({ number, tasks }))
      .sort((a, b) => a.number - b.number);
  }

  /**
   * Calculate execution waves based on dependencies
   *
   * Rules:
   * 1. parallel_safe: false → always sequential (own wave)
   * 2. parallel_safe: true + depends_on: [] → can run immediately
   * 3. parallel_safe: true + depends_on: [X] → can run after X completes
   * 4. Tasks within same phase are considered for parallelization
   */
  private calculateWaves(tasks: TaskNode[]): ExecutionWave[] {
    const waves: ExecutionWave[] = [];
    const completed = new Set<string>();
    let remaining = tasks.filter(t => t.status !== 'complete');
    let waveNumber = 1;

    // Mark already completed tasks
    tasks.filter(t => t.status === 'complete').forEach(t => completed.add(t.planId));

    while (remaining.length > 0) {
      // Find tasks whose dependencies are all satisfied
      const ready = remaining.filter(t =>
        t.dependsOn.every(dep => completed.has(dep))
      );

      if (ready.length === 0) {
        // Check for circular dependency
        const remainingIds = remaining.map(t => t.planId).join(', ');
        throw new Error(`Circular dependency detected. Stuck tasks: ${remainingIds}`);
      }

      // Separate parallel-safe and sequential tasks
      const parallelTasks = ready.filter(t => t.parallelSafe);
      const sequentialTasks = ready.filter(t => !t.parallelSafe);

      // Add parallel tasks as one wave (if any)
      if (parallelTasks.length > 0) {
        waves.push({
          waveNumber: waveNumber++,
          tasks: parallelTasks.map(t => t.id),
          isParallel: parallelTasks.length > 1
        });
        parallelTasks.forEach(t => completed.add(t.planId));
        remaining = remaining.filter(t => !parallelTasks.includes(t));
      }

      // Add sequential tasks as individual waves
      for (const task of sequentialTasks) {
        waves.push({
          waveNumber: waveNumber++,
          tasks: [task.id],
          isParallel: false
        });
        completed.add(task.planId);
        remaining = remaining.filter(t => t.id !== task.id);
      }
    }

    return waves;
  }

  /**
   * Check if a specific task can be executed
   */
  canExecute(taskId: string, completedTasks: Set<string>, tasks: TaskNode[]): boolean {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return false;
    return task.dependsOn.every(dep => completedTasks.has(dep));
  }

  /**
   * Get tasks that are blocked and what they're waiting for
   */
  getBlockedTasks(tasks: TaskNode[], completedTasks: Set<string>): { taskId: string; waitingFor: string[] }[] {
    return tasks
      .filter(t => t.status !== 'complete' && !this.canExecute(t.id, completedTasks, tasks))
      .map(t => ({
        taskId: t.id,
        waitingFor: t.dependsOn.filter(dep => !completedTasks.has(dep))
      }));
  }
}

export default GsdDependencyAnalyzer;
