/**
 * GSD (Get Shit Done) Service
 *
 * TypeScript-based ROADMAP.md parser and kanban sync service
 * Parses .planning/ROADMAP.md and Phase plans without Python dependency
 */

import * as fs from 'fs';
import * as path from 'path';
import { logger } from './app-logger';

export interface GsdRoadmapInfo {
  phases: GsdPhaseInfo[];
  current_phase: number;
  total_phases: number;
  progress_percent: number;
}

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

export interface GsdPlanInfo {
  id: string;
  name: string;
  path: string;
  tasks: number;
  completed: number;
  status: 'complete' | 'in_progress' | 'not_started';
}

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

export interface GsdSyncResult {
  success: boolean;
  tasks?: GsdTask[];
  error?: string;
  task_count?: number;
}

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

export interface GsdProgressInfo {
  total_phases: number;
  completed_phases: number;
  percent: number;
  current_phase: number;
}

// LeaderContext types for CEO Dashboard
export interface GsdGoal {
  id: string;
  title: string;
  description: string;
  priority: 'primary' | 'secondary' | 'tertiary';
  status: 'active' | 'achieved' | 'abandoned';
  phase?: number;
}

export interface GsdDecision {
  id: string;
  title: string;
  description: string;
  rationale: string;
  made_at: string;
  phase?: number;
}

export interface GsdPattern {
  id: string;
  name: string;
  description: string;
  category: string;
  occurrences: number;
}

export interface GsdMistake {
  id: string;
  description: string;
  impact: string;
  lesson_learned: string;
  occurred_at: string;
  phase?: number;
}

export interface GsdRisk {
  id: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  likelihood: 'unlikely' | 'possible' | 'likely' | 'certain';
  mitigation?: string;
  status: 'identified' | 'mitigated' | 'occurred' | 'closed';
}

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

// SharedBoard types for CEO Team Kanban
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

export interface GsdTeamLane {
  team_id: string;
  team_name: string;
  tasks: GsdTeamTask[];
  total_tasks: number;
  completed_tasks: number;
  blocked_tasks: number;
}

export interface GsdSharedBoard {
  id: string;
  name: string;
  phase: number;
  lanes: GsdTeamLane[];
  created_at: string;
  updated_at: string;
}

export class GsdService {
  private projectPath: string;

  constructor(projectPath: string) {
    this.projectPath = projectPath;
  }

  /**
   * Parse ROADMAP.md and return phase information
   */
  async getRoadmap(roadmapPath: string = '.planning/ROADMAP.md'): Promise<GsdRoadmapInfo> {
    const fullPath = path.join(this.projectPath, roadmapPath);

    if (!fs.existsSync(fullPath)) {
      logger.warn(`ROADMAP.md not found at ${fullPath}`);
      return {
        phases: [],
        current_phase: 0,
        total_phases: 0,
        progress_percent: 0
      };
    }

    try {
      const content = fs.readFileSync(fullPath, 'utf-8');
      return this.parseRoadmap(content, roadmapPath);
    } catch (error) {
      logger.error('Failed to parse ROADMAP.md:', error);
      throw error;
    }
  }

  /**
   * Parse STATE.md and return state information
   */
  async getState(statePath: string = '.planning/STATE.md'): Promise<GsdStateInfo | null> {
    const fullPath = path.join(this.projectPath, statePath);

    if (!fs.existsSync(fullPath)) {
      logger.warn(`STATE.md not found at ${fullPath}`);
      return null;
    }

    try {
      const content = fs.readFileSync(fullPath, 'utf-8');
      return this.parseState(content);
    } catch (error) {
      logger.error('Failed to parse STATE.md:', error);
      throw error;
    }
  }

  /**
   * Parse STATE.md content
   */
  private parseState(content: string): GsdStateInfo {
    // Parse Current focus
    const focusMatch = /\*\*Current focus:\*\* (.+)/.exec(content);

    // Parse Current Position section
    const phaseMatch = /Phase: (\d+) of (\d+) \(([^)]+)\)/.exec(content);
    const statusMatch = /Status: (.+)/.exec(content);
    const planProgressMatch = /Plan: (.+)/.exec(content);

    // Parse Performance Metrics
    const totalPlansMatch = /Total plans completed: (\d+)/.exec(content);
    const avgDurationMatch = /Average duration: (.+)/.exec(content);
    const totalTimeMatch = /Total execution time: (.+)/.exec(content);

    // Parse Recent Trend
    const trendMatch = /Last \d+ plans: (.+)/.exec(content);

    // Parse Session Continuity
    const lastSessionMatch = /Last session: (.+)/.exec(content);
    const stoppedAtMatch = /Stopped at: (.+)/.exec(content);
    const resumeFileMatch = /Resume file: (.+)/.exec(content);

    // Parse Next Steps
    const nextStepsMatch = /## Next Steps\n\n([\s\S]*?)(?=##|$)/.exec(content);
    const nextSteps = nextStepsMatch
      ? nextStepsMatch[1].split('\n').filter(l => l.startsWith('- ') || /^\d+\./.test(l.trim())).map(l => l.replace(/^[-\d.]+\s*/, '').trim())
      : [];

    return {
      current_focus: focusMatch?.[1] || '',
      current_position: {
        phase: parseInt(phaseMatch?.[1] || '0'),
        total_phases: parseInt(phaseMatch?.[2] || '0'),
        phase_name: phaseMatch?.[3] || '',
        status: statusMatch?.[1] || '',
        plan_progress: planProgressMatch?.[1] || ''
      },
      performance_metrics: {
        total_plans_completed: parseInt(totalPlansMatch?.[1] || '0'),
        average_duration: avgDurationMatch?.[1] || '',
        total_execution_time: totalTimeMatch?.[1] || ''
      },
      recent_trend: trendMatch?.[1]?.split(',').map(s => s.trim()) || [],
      session_continuity: {
        last_session: lastSessionMatch?.[1] || '',
        stopped_at: stoppedAtMatch?.[1] || '',
        resume_file: resumeFileMatch?.[1] === 'None' ? null : (resumeFileMatch?.[1] || null)
      },
      next_steps: nextSteps
    };
  }

  /**
   * Get detailed information about a specific plan
   */
  async getPlanDetail(planPath: string): Promise<GsdPlanDetail | null> {
    const fullPath = path.join(this.projectPath, planPath);

    if (!fs.existsSync(fullPath)) {
      logger.warn(`PLAN.md not found at ${fullPath}`);
      return null;
    }

    try {
      const content = fs.readFileSync(fullPath, 'utf-8');
      return this.parsePlanDetail(content, planPath);
    } catch (error) {
      logger.error('Failed to parse plan detail:', error);
      return null;
    }
  }

  /**
   * Parse PLAN.md content into detailed structure
   */
  private parsePlanDetail(content: string, planPath: string): GsdPlanDetail {
    // Parse frontmatter
    const frontmatter = this.parseFrontmatter(content);

    // Parse objective
    const objectiveMatch = /<objective>([\s\S]*?)<\/objective>/.exec(content);
    const objective = objectiveMatch?.[1]?.trim() || '';

    // Parse context
    const contextMatch = /<context>([\s\S]*?)<\/context>/.exec(content);
    const context = contextMatch?.[1]?.trim() || '';

    // Parse tasks
    const tasks = this.parseTaskDetails(content);

    // Parse verification
    const verificationMatch = /<verification>([\s\S]*?)<\/verification>/.exec(content);
    const verification = verificationMatch?.[1]?.trim() || '';

    // Parse success criteria
    const successMatch = /<success_criteria>([\s\S]*?)<\/success_criteria>/.exec(content);
    const successCriteria = successMatch?.[1]
      ?.split('\n')
      .filter(l => l.trim().startsWith('- [ ]') || l.trim().startsWith('- [x]'))
      .map(l => l.replace(/^- \[[ x]\] /, '').trim()) || [];

    // Parse output files
    const outputMatch = /<output>([\s\S]*?)<\/output>/.exec(content);
    const outputFiles = outputMatch?.[1]
      ?.split('\n')
      .filter(l => l.trim().startsWith('-'))
      .map(l => l.replace(/^- /, '').trim().replace(/`/g, '')) || [];

    // Check for SUMMARY file to determine task completion
    const summaryPath = planPath.replace('-PLAN.md', '-SUMMARY.md').replace('PLAN-', '').replace('.md', '-SUMMARY.md');
    const summaryExists = fs.existsSync(path.join(this.projectPath, summaryPath));

    // Mark all tasks as completed if summary exists
    if (summaryExists) {
      tasks.forEach(task => task.completed = true);
    }

    return {
      id: `${frontmatter.phase}-${String(frontmatter.plan).padStart(2, '0')}`,
      name: String(frontmatter.name || ''),
      phase: Number(frontmatter.phase) || 0,
      plan: Number(frontmatter.plan) || 0,
      path: planPath,
      estimated_minutes: Number(frontmatter.estimated_minutes) || 15,
      parallel_safe: Boolean(frontmatter.parallel_safe),
      depends_on: frontmatter.depends_on ? String(frontmatter.depends_on) : undefined,
      objective,
      context,
      tasks,
      verification,
      success_criteria: successCriteria,
      output_files: outputFiles
    };
  }

  /**
   * Parse task details from PLAN.md content
   */
  private parseTaskDetails(content: string): GsdTaskDetail[] {
    const tasks: GsdTaskDetail[] = [];
    const taskRegex = /<task\s+type="([^"]+)">([\s\S]*?)<\/task>/g;
    let match;
    let taskIndex = 1;

    while ((match = taskRegex.exec(content)) !== null) {
      const taskType = match[1];
      const taskContent = match[2];

      const name = this.extractXmlTag(taskContent, 'name') || `Task ${taskIndex}`;
      const files = this.extractXmlTag(taskContent, 'files')?.split(',').map(f => f.trim()) || [];
      const action = this.extractXmlTag(taskContent, 'action') || '';
      const verify = this.extractXmlTag(taskContent, 'verify') || '';
      const done = this.extractXmlTag(taskContent, 'done') || '';

      tasks.push({
        id: `task-${taskIndex}`,
        type: taskType,
        name,
        files,
        action,
        verify,
        done_criteria: done,
        completed: false // Will be determined by SUMMARY existence
      });

      taskIndex++;
    }

    return tasks;
  }

  /**
   * Parse ROADMAP.md content
   */
  private parseRoadmap(content: string, roadmapPath: string): GsdRoadmapInfo {
    const phases: GsdPhaseInfo[] = [];

    // Parse phases from the Phases section
    // Match patterns like:
    // - [x] **Phase 1: Foundation** - description
    // - [ ] **Phase 2: Architecture** - description
    const phaseRegex = /- \[(x| )\] \*\*Phase (\d+(?:\.\d+)?): ([^*]+)\*\* - ([^\n]+)/g;
    let match;

    while ((match = phaseRegex.exec(content)) !== null) {
      const isComplete = match[1] === 'x';
      const phaseNumber = parseFloat(match[2]);
      const phaseName = match[3].trim();
      const phaseGoal = match[4].trim().replace(/✓$/, '').trim();

      // Get plans for this phase from Phase Details section
      const plans = this.parsePhasePlans(content, phaseNumber, roadmapPath);
      const completedPlans = plans.filter(p => p.status === 'complete').length;

      // Determine phase status
      let status: 'complete' | 'in_progress' | 'not_started';
      if (isComplete) {
        status = 'complete';
      } else if (plans.some(p => p.status === 'in_progress') || completedPlans > 0) {
        status = 'in_progress';
      } else {
        status = 'not_started';
      }

      // Parse depends_on from Phase Details
      const dependsOn = this.parsePhaseDepends(content, phaseNumber);

      phases.push({
        number: phaseNumber,
        name: phaseName,
        goal: phaseGoal,
        status,
        depends_on: dependsOn,
        plans,
        completed_plans: completedPlans,
        total_plans: plans.length
      });
    }

    // Calculate current phase (first non-complete phase)
    const currentPhase = phases.find(p => p.status !== 'complete')?.number || (phases.length > 0 ? phases[phases.length - 1].number : 0);

    // Calculate progress
    const completedPhases = phases.filter(p => p.status === 'complete').length;
    const progressPercent = phases.length > 0 ? Math.round((completedPhases / phases.length) * 100) : 0;

    return {
      phases,
      current_phase: currentPhase,
      total_phases: phases.length,
      progress_percent: progressPercent
    };
  }

  /**
   * Parse plans for a specific phase from Phase Details section
   */
  private parsePhasePlans(content: string, phaseNumber: number, roadmapPath: string): GsdPlanInfo[] {
    const plans: GsdPlanInfo[] = [];

    // Find the Phase Details section for this phase
    // Look for "Plans:" at the start of a line (not **Plans**:) followed by the list
    const phaseDetailRegex = new RegExp(
      `### Phase ${phaseNumber}[\\s\\S]*?(?:^|\\n)Plans:\\s*\\n([\\s\\S]*?)(?=###|$)`,
      'm'
    );
    const phaseMatch = phaseDetailRegex.exec(content);

    if (!phaseMatch) {
      logger.debug(`No plans section found for Phase ${phaseNumber}`);
      return plans;
    }

    const plansSection = phaseMatch[1];

    // Parse plan entries like:
    // - [x] 01-01: Auto-Claude 코드베이스 분석 ✓
    // - [ ] 04-01: 라우터 코어 구현
    const planRegex = /- \[(x| )\] (\d{2}-\d{2}): ([^\n✓]+)(?:✓)?/g;
    let planMatch;

    while ((planMatch = planRegex.exec(plansSection)) !== null) {
      const isComplete = planMatch[1] === 'x';
      const planId = planMatch[2].trim();
      const planName = planMatch[3].trim();

      // Construct plan path
      const phaseStr = String(phaseNumber).padStart(2, '0');
      const planDir = path.dirname(roadmapPath);
      const planPath = path.join(planDir, `phases/${phaseStr}-*/PLAN-${planId}.md`);

      // Try to find actual plan file and count tasks
      const planInfo = this.findPlanFile(phaseNumber, planId, roadmapPath);

      plans.push({
        id: planId,
        name: planName,
        path: planInfo?.path || planPath,
        tasks: planInfo?.tasks || 0,
        completed: planInfo?.completed || 0,
        status: isComplete ? 'complete' : (planInfo?.completed || 0) > 0 ? 'in_progress' : 'not_started'
      });
    }

    return plans;
  }

  /**
   * Find plan file and count tasks
   */
  private findPlanFile(phaseNumber: number, planId: string, roadmapPath: string): { path: string; tasks: number; completed: number } | null {
    const planDir = path.join(this.projectPath, path.dirname(roadmapPath));
    const phaseStr = String(phaseNumber).padStart(2, '0');

    // Look for phase directory
    const phaseDirs = fs.readdirSync(planDir, { withFileTypes: true })
      .filter(d => d.isDirectory() && d.name.startsWith(`phases`));

    for (const phaseDir of phaseDirs) {
      const fullPhaseDir = path.join(planDir, phaseDir.name);
      const subDirs = fs.existsSync(fullPhaseDir) ? fs.readdirSync(fullPhaseDir, { withFileTypes: true })
        .filter(d => d.isDirectory() && d.name.startsWith(phaseStr)) : [];

      for (const subDir of subDirs) {
        // Try both naming conventions:
        // 1. PLAN-01-01.md (original format)
        // 2. 01-01-PLAN.md (alternative format)
        const planFilePath1 = path.join(fullPhaseDir, subDir.name, `PLAN-${planId}.md`);
        const planFilePath2 = path.join(fullPhaseDir, subDir.name, `${planId}-PLAN.md`);

        let planFilePath: string | null = null;
        if (fs.existsSync(planFilePath1)) {
          planFilePath = planFilePath1;
        } else if (fs.existsSync(planFilePath2)) {
          planFilePath = planFilePath2;
        }

        if (planFilePath) {
          const taskInfo = this.countPlanTasks(planFilePath);
          return {
            path: planFilePath,
            tasks: taskInfo.total,
            completed: taskInfo.completed
          };
        }

        // Also check for SUMMARY file for this plan (indicates completion)
        const summaryFilePath = path.join(fullPhaseDir, subDir.name, `${planId}-SUMMARY.md`);
        if (fs.existsSync(summaryFilePath)) {
          // If summary exists, plan is complete
          return {
            path: summaryFilePath,
            tasks: 1,
            completed: 1
          };
        }
      }
    }

    return null;
  }

  /**
   * Count tasks in a PLAN.md file
   */
  private countPlanTasks(planPath: string): { total: number; completed: number } {
    try {
      const content = fs.readFileSync(planPath, 'utf-8');

      // Count <task> elements
      const taskMatches = content.match(/<task[^>]*>/g);
      const total = taskMatches?.length || 0;

      // Count completed tasks (status="done" or similar)
      const completedMatches = content.match(/<task[^>]*status="(done|complete)"[^>]*>/gi);
      const completed = completedMatches?.length || 0;

      return { total, completed };
    } catch {
      return { total: 0, completed: 0 };
    }
  }

  /**
   * Parse depends_on from Phase Details
   */
  private parsePhaseDepends(content: string, phaseNumber: number): number | undefined {
    const dependsRegex = new RegExp(
      `### Phase ${phaseNumber}[^#]*?\\*\\*Depends on\\*\\*: Phase (\\d+)`,
      's'
    );
    const match = dependsRegex.exec(content);
    return match ? parseInt(match[1], 10) : undefined;
  }

  /**
   * Calculate phase progress
   */
  async getPhaseProgress(roadmapPath: string = '.planning/ROADMAP.md'): Promise<GsdProgressInfo> {
    const roadmap = await this.getRoadmap(roadmapPath);

    const completedPhases = roadmap.phases.filter(p => p.status === 'complete').length;

    return {
      total_phases: roadmap.total_phases,
      completed_phases: completedPhases,
      percent: roadmap.progress_percent,
      current_phase: roadmap.current_phase
    };
  }

  /**
   * Sync a PLAN.md to kanban board
   * Creates tasks in .auto-claude/specs/ from PLAN.md tasks
   */
  async syncPlanToKanban(planPath: string): Promise<GsdSyncResult> {
    const fullPath = path.join(this.projectPath, planPath);

    if (!fs.existsSync(fullPath)) {
      return {
        success: false,
        error: `Plan file not found: ${planPath}`
      };
    }

    try {
      const content = fs.readFileSync(fullPath, 'utf-8');
      const tasks = this.parsePlanTasks(content, planPath);

      // Create spec files for each task
      const autoClaudeDir = path.join(this.projectPath, '.auto-claude', 'specs');
      if (!fs.existsSync(autoClaudeDir)) {
        fs.mkdirSync(autoClaudeDir, { recursive: true });
      }

      const createdTasks: GsdTask[] = [];

      for (const task of tasks) {
        // Create spec directory
        const specId = `${task.phase}-${String(task.task_number).padStart(2, '0')}-${this.slugify(task.title)}`;
        const specDir = path.join(autoClaudeDir, specId);

        if (!fs.existsSync(specDir)) {
          fs.mkdirSync(specDir, { recursive: true });

          // Create spec.md
          const specContent = this.generateSpecContent(task);
          fs.writeFileSync(path.join(specDir, 'spec.md'), specContent);

          // Create implementation_plan.json
          const planJson = this.generateImplementationPlan(task, specId);
          fs.writeFileSync(path.join(specDir, 'implementation_plan.json'), JSON.stringify(planJson, null, 2));

          createdTasks.push(task);
        }
      }

      return {
        success: true,
        tasks: createdTasks,
        task_count: createdTasks.length
      };
    } catch (error) {
      logger.error('Failed to sync plan to kanban:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Parse tasks from PLAN.md content
   */
  private parsePlanTasks(content: string, planPath: string): GsdTask[] {
    const tasks: GsdTask[] = [];

    // Parse frontmatter for phase/plan info
    const frontmatter = this.parseFrontmatter(content);
    const phase = frontmatter.phase || this.extractPhaseFromPath(planPath);
    const plan = frontmatter.plan || this.extractPlanFromPath(planPath);

    // Parse <task> elements
    const taskRegex = /<task\s+type="([^"]+)">([\s\S]*?)<\/task>/g;
    let match;
    let taskNumber = 1;

    while ((match = taskRegex.exec(content)) !== null) {
      const taskType = match[1];
      const taskContent = match[2];

      const name = this.extractXmlTag(taskContent, 'name');
      const files = this.extractXmlTag(taskContent, 'files')?.split(',').map(f => f.trim()) || [];
      const action = this.extractXmlTag(taskContent, 'action') || '';
      const verify = this.extractXmlTag(taskContent, 'verify') || '';
      const done = this.extractXmlTag(taskContent, 'done') || '';

      const now = new Date().toISOString();

      tasks.push({
        id: `${phase}-${plan}-${taskNumber}`,
        title: name || `Task ${taskNumber}`,
        description: action,
        status: 'pending',
        phase: String(phase),
        plan: String(plan),
        task_number: taskNumber,
        files,
        action,
        verify,
        done_criteria: done,
        gsd_task_type: taskType,
        created_at: now,
        updated_at: now,
        metadata: {
          source: 'gsd',
          plan_path: planPath
        }
      });

      taskNumber++;
    }

    return tasks;
  }

  /**
   * Parse YAML frontmatter
   */
  private parseFrontmatter(content: string): Record<string, unknown> {
    const match = /^---\s*\n([\s\S]*?)\n---/.exec(content);
    if (!match) return {};

    const yaml = match[1];
    const result: Record<string, unknown> = {};

    // Simple YAML parsing (key: value)
    yaml.split('\n').forEach(line => {
      const kvMatch = /^(\w+):\s*(.*)$/.exec(line.trim());
      if (kvMatch) {
        const [, key, value] = kvMatch;
        // Try to parse as number
        const numValue = parseFloat(value);
        result[key] = isNaN(numValue) ? value : numValue;
      }
    });

    return result;
  }

  /**
   * Extract content from XML-style tag
   */
  private extractXmlTag(content: string, tag: string): string | null {
    const regex = new RegExp(`<${tag}[^>]*>([\\s\\S]*?)</${tag}>`, 'i');
    const match = regex.exec(content);
    return match ? match[1].trim() : null;
  }

  /**
   * Extract phase number from path
   */
  private extractPhaseFromPath(planPath: string): string {
    const match = /(\d{2})-/.exec(path.basename(path.dirname(planPath)));
    return match ? match[1] : '00';
  }

  /**
   * Extract plan number from path
   */
  private extractPlanFromPath(planPath: string): string {
    const match = /PLAN-(\d{2}-\d{2})/.exec(path.basename(planPath));
    return match ? match[1] : '00-00';
  }

  /**
   * Generate spec.md content from task
   */
  private generateSpecContent(task: GsdTask): string {
    return `# ${task.title}

## Overview

${task.description}

## Source

- Phase: ${task.phase}
- Plan: ${task.plan}
- Task Type: ${task.gsd_task_type}

## Files

${task.files.map(f => `- ${f}`).join('\n')}

## Success Criteria

${task.done_criteria}

## Verification

${task.verify}
`;
  }

  /**
   * Generate implementation_plan.json from task
   */
  private generateImplementationPlan(task: GsdTask, specId: string): Record<string, unknown> {
    return {
      spec_id: specId,
      subtasks: [{
        id: '1',
        title: task.title,
        description: task.description,
        files: task.files,
        status: 'pending',
        dependencies: []
      }]
    };
  }

  /**
   * Create URL-safe slug from string
   */
  private slugify(text: string): string {
    return text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
      .substring(0, 50);
  }

  /**
   * Sync entire phase to kanban
   */
  async syncPhaseToKanban(phaseNumber: number): Promise<GsdSyncResult> {
    const roadmap = await this.getRoadmap();
    const phase = roadmap.phases.find(p => p.number === phaseNumber);

    if (!phase) {
      return {
        success: false,
        error: `Phase ${phaseNumber} not found`
      };
    }

    const allTasks: GsdTask[] = [];

    for (const plan of phase.plans) {
      if (plan.path && fs.existsSync(path.join(this.projectPath, plan.path))) {
        const result = await this.syncPlanToKanban(plan.path);
        if (result.success && result.tasks) {
          allTasks.push(...result.tasks);
        }
      }
    }

    return {
      success: true,
      tasks: allTasks,
      task_count: allTasks.length
    };
  }

  /**
   * Update task status
   */
  async updateTaskStatus(taskId: string, status: string): Promise<boolean> {
    // Find and update the task in .auto-claude/specs/
    const specsDir = path.join(this.projectPath, '.auto-claude', 'specs');

    if (!fs.existsSync(specsDir)) {
      return false;
    }

    const specDirs = fs.readdirSync(specsDir, { withFileTypes: true })
      .filter(d => d.isDirectory());

    for (const dir of specDirs) {
      const planPath = path.join(specsDir, dir.name, 'implementation_plan.json');
      if (fs.existsSync(planPath)) {
        try {
          const plan = JSON.parse(fs.readFileSync(planPath, 'utf-8'));
          const subtask = plan.subtasks?.find((s: { id: string }) => s.id === taskId);

          if (subtask) {
            subtask.status = status;
            fs.writeFileSync(planPath, JSON.stringify(plan, null, 2));
            return true;
          }
        } catch {
          continue;
        }
      }
    }

    return false;
  }

  /**
   * Generate summary from completed tasks
   */
  async generateSummary(planPath: string): Promise<string | null> {
    const fullPath = path.join(this.projectPath, planPath);

    if (!fs.existsSync(fullPath)) {
      return null;
    }

    try {
      const content = fs.readFileSync(fullPath, 'utf-8');
      const tasks = this.parsePlanTasks(content, planPath);

      // Generate summary content
      const summaryContent = `# Summary

## Completed Tasks

${tasks.map(t => `- [x] ${t.title}`).join('\n')}

## Files Modified

${[...new Set(tasks.flatMap(t => t.files))].map(f => `- ${f}`).join('\n')}

## Generated

Date: ${new Date().toISOString()}
Source: ${planPath}
`;

      // Write summary file
      const summaryPath = fullPath.replace('PLAN-', '').replace('.md', '-SUMMARY.md');
      fs.writeFileSync(summaryPath, summaryContent);

      return summaryPath;
    } catch (error) {
      logger.error('Failed to generate summary:', error);
      return null;
    }
  }

  /**
   * Get sync status
   */
  async getSyncStatus(): Promise<Record<string, unknown>> {
    const specsDir = path.join(this.projectPath, '.auto-claude', 'specs');

    if (!fs.existsSync(specsDir)) {
      return {
        synced_tasks: 0,
        pending_tasks: 0,
        last_sync: null
      };
    }

    const specDirs = fs.readdirSync(specsDir, { withFileTypes: true })
      .filter(d => d.isDirectory());

    let pendingTasks = 0;
    let completedTasks = 0;

    for (const dir of specDirs) {
      const planPath = path.join(specsDir, dir.name, 'implementation_plan.json');
      if (fs.existsSync(planPath)) {
        try {
          const plan = JSON.parse(fs.readFileSync(planPath, 'utf-8'));
          for (const subtask of plan.subtasks || []) {
            if (subtask.status === 'completed') {
              completedTasks++;
            } else {
              pendingTasks++;
            }
          }
        } catch {
          continue;
        }
      }
    }

    return {
      synced_tasks: specDirs.length,
      pending_tasks: pendingTasks,
      completed_tasks: completedTasks,
      last_sync: new Date().toISOString()
    };
  }

  /**
   * Get SharedBoard data for CEO Team Kanban visualization
   */
  async getSharedBoard(phase?: number): Promise<GsdSharedBoard | null> {
    const boardDir = path.join(this.projectPath, '.planning', 'team_sync', 'shared_board');

    if (!fs.existsSync(boardDir)) {
      logger.debug(`SharedBoard directory not found at ${boardDir}`);
      return null;
    }

    try {
      // Find board file (latest or specific phase)
      const files = fs.readdirSync(boardDir).filter(f => f.endsWith('.json'));

      if (files.length === 0) {
        logger.debug('No board files found in SharedBoard directory');
        return null;
      }

      // Sort by modification time, get latest
      const latestFile = files
        .map(f => ({ name: f, mtime: fs.statSync(path.join(boardDir, f)).mtime }))
        .sort((a, b) => b.mtime.getTime() - a.mtime.getTime())[0];

      const content = fs.readFileSync(path.join(boardDir, latestFile.name), 'utf-8');
      const data = JSON.parse(content);

      return this.transformBoardData(data);
    } catch (error) {
      logger.error('Failed to load SharedBoard:', error);
      return null;
    }
  }

  /**
   * Transform raw board data to GsdSharedBoard format
   */
  private transformBoardData(data: Record<string, unknown>): GsdSharedBoard {
    const lanes = data.lanes as Array<Record<string, unknown>> || [];

    return {
      id: String(data.id || ''),
      name: String(data.name || ''),
      phase: Number(data.phase) || 0,
      lanes: lanes.map((lane) => {
        const tasks = lane.tasks as Array<Record<string, unknown>> || [];
        return {
          team_id: String(lane.team_id || ''),
          team_name: String(lane.team_name || lane.team_id || ''),
          tasks: tasks.map((task) => ({
            id: String(task.id || ''),
            team_id: String(task.team_id || ''),
            title: String(task.title || ''),
            description: String(task.description || ''),
            status: (task.status as GsdTeamTask['status']) || 'not_started',
            progress: Number(task.progress) || 0,
            depends_on: Array.isArray(task.depends_on) ? task.depends_on.map(String) : [],
            blocking: Array.isArray(task.blocking) ? task.blocking.map(String) : [],
            assignee: task.assignee ? String(task.assignee) : undefined,
            priority: Number(task.priority) || 3
          })),
          total_tasks: tasks.length,
          completed_tasks: tasks.filter((t) => t.status === 'completed').length,
          blocked_tasks: tasks.filter((t) => t.status === 'blocked').length
        };
      }),
      created_at: String(data.created_at || new Date().toISOString()),
      updated_at: String(data.updated_at || new Date().toISOString())
    };
  }

  /**
   * Get LeaderContext data for CEO Dashboard visualization
   */
  async getLeaderContext(phase?: number): Promise<GsdLeaderContext | null> {
    const contextDir = path.join(this.projectPath, '.planning', 'leader_context');

    if (!fs.existsSync(contextDir)) {
      logger.debug(`LeaderContext directory not found at ${contextDir}`);
      return null;
    }

    try {
      // Find context file
      const files = fs.readdirSync(contextDir).filter(f => f.endsWith('.json'));

      if (files.length === 0) {
        logger.debug('No context files found in leader_context directory');
        return null;
      }

      // Get latest context file
      const latestFile = files
        .map(f => ({ name: f, mtime: fs.statSync(path.join(contextDir, f)).mtime }))
        .sort((a, b) => b.mtime.getTime() - a.mtime.getTime())[0];

      const content = fs.readFileSync(path.join(contextDir, latestFile.name), 'utf-8');
      const data = JSON.parse(content);

      return this.transformContextData(data);
    } catch (error) {
      logger.error('Failed to load LeaderContext:', error);
      return null;
    }
  }

  /**
   * Transform raw context data to GsdLeaderContext format
   */
  private transformContextData(data: Record<string, unknown>): GsdLeaderContext {
    const goals = data.goals as Array<Record<string, unknown>> || [];
    const decisions = data.decisions as Array<Record<string, unknown>> || [];
    const patterns = data.patterns as Array<Record<string, unknown>> || [];
    const mistakes = data.mistakes as Array<Record<string, unknown>> || [];
    const risks = data.risks as Array<Record<string, unknown>> || [];

    return {
      project_id: String(data.project_id || 'unknown'),
      phase: Number(data.phase) || 0,
      goals: goals.map((g) => ({
        id: String(g.id || ''),
        title: String(g.title || ''),
        description: String(g.description || ''),
        priority: (g.priority as GsdGoal['priority']) || 'secondary',
        status: (g.status as GsdGoal['status']) || 'active',
        phase: g.phase ? Number(g.phase) : undefined
      })),
      decisions: decisions.map((d) => ({
        id: String(d.id || ''),
        title: String(d.title || ''),
        description: String(d.description || ''),
        rationale: String(d.rationale || ''),
        made_at: String(d.made_at || d.created_at || ''),
        phase: d.phase ? Number(d.phase) : undefined
      })),
      patterns: patterns.map((p) => ({
        id: String(p.id || ''),
        name: String(p.name || ''),
        description: String(p.description || ''),
        category: String(p.category || 'general'),
        occurrences: Number(p.occurrences) || 1
      })),
      mistakes: mistakes.map((m) => ({
        id: String(m.id || ''),
        description: String(m.description || ''),
        impact: String(m.impact || ''),
        lesson_learned: String(m.lesson_learned || ''),
        occurred_at: String(m.occurred_at || m.created_at || ''),
        phase: m.phase ? Number(m.phase) : undefined
      })),
      risks: risks.map((r) => ({
        id: String(r.id || ''),
        title: String(r.title || ''),
        description: String(r.description || ''),
        severity: (r.severity as GsdRisk['severity']) || 'medium',
        likelihood: (r.likelihood as GsdRisk['likelihood']) || 'possible',
        mitigation: r.mitigation ? String(r.mitigation) : undefined,
        status: (r.status as GsdRisk['status']) || 'identified'
      })),
      updated_at: String(data.updated_at || new Date().toISOString())
    };
  }
}
