/**
 * CEO Service - Agent loader and router
 *
 * TypeScript implementation of CEO agent loading and task routing
 */

import * as fs from 'fs';
import * as path from 'path';
import { logger } from './app-logger';

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

// Coding-related keywords
const CODING_KEYWORDS = [
  // Korean
  '코드', '개발', '구현', '만들어', '작성', '수정',
  'API', '함수', '클래스', '버그', '디버그', '테스트',
  '빌드', '배포', '웹사이트', '앱', '서버', '프로그래밍',
  // English
  'code', 'develop', 'implement', 'create', 'build', 'write',
  'fix', 'function', 'class', 'bug', 'debug', 'test',
  'deploy', 'website', 'app', 'server', 'programming',
  'software', 'script', 'module', 'package', 'library'
];

// Non-coding related keywords
const NON_CODING_KEYWORDS = [
  // Korean
  '기획', '분석', '리포트', '문서', '계약', '법률',
  '마케팅', '블로그', 'SEO', '영업', '제안서', '견적',
  '회의', '조사', '연구', '보고서', '데이터', '디자인',
  '예산', '세금', '회계',
  // English
  'plan', 'planning', 'analysis', 'report', 'document', 'contract',
  'legal', 'marketing', 'blog', 'sales', 'proposal', 'quote',
  'meeting', 'research', 'survey', 'design', 'budget', 'tax',
  'accounting', 'strategy', 'communication', 'writing'
];

// Team keywords for routing
const TEAM_KEYWORDS: Record<string, string[]> = {
  'planning/leader': ['기획', '요구사항', '분석', 'plan', 'requirement', 'analysis', 'strategy'],
  'marketing/leader': ['마케팅', '블로그', 'SEO', '콘텐츠', 'marketing', 'blog', 'content', 'social'],
  'legal/leader': ['계약', '법률', '법무', 'contract', 'legal', 'compliance'],
  'finance/leader': ['회계', '세금', '재무', '예산', 'finance', 'accounting', 'tax', 'budget'],
  'design/leader': ['디자인', 'UI', 'UX', 'design', 'wireframe', 'mockup', 'visual'],
  'sales/leader': ['영업', '제안서', '견적', 'sales', 'proposal', 'quote', 'client'],
  'data/leader': ['데이터', '리포트', '분석', 'data', 'report', 'analytics', 'metrics'],
  'security/leader': ['보안', '취약점', 'security', 'vulnerability', 'audit'],
  'support/leader': ['문의', '지원', '도움', 'support', 'help', 'customer']
};

export class CeoService {
  private projectPath: string;
  private agents: Record<string, AgentDefinition> = {};
  private teams: Record<string, TeamInfo> = {};

  constructor(projectPath: string) {
    this.projectPath = projectPath;
  }

  /**
   * Find agents directory in project
   */
  private findAgentsDir(): string | null {
    const candidates = [
      path.join(this.projectPath, '.claude', 'agents'),
      path.join(this.projectPath, 'ceo-agents')
    ];

    for (const candidate of candidates) {
      if (fs.existsSync(candidate)) {
        return candidate;
      }
    }

    return null;
  }

  /**
   * Load all agent definitions
   */
  async loadAgents(): Promise<LoadedAgentsData> {
    const agentsDir = this.findAgentsDir();
    if (!agentsDir) {
      logger.warn('No agents directory found');
      return { agents: {}, teams: {} };
    }

    this.agents = {};
    this.teams = {};

    try {
      this.walkDirectory(agentsDir, agentsDir);
    } catch (error) {
      logger.error('Failed to load agents:', error);
    }

    return {
      agents: this.agents,
      teams: this.teams
    };
  }

  /**
   * Walk directory and load agent files
   */
  private walkDirectory(dir: string, baseDir: string): void {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        this.walkDirectory(fullPath, baseDir);
      } else if (entry.name.endsWith('.md')) {
        try {
          const agent = this.parseAgentFile(fullPath, baseDir);
          if (agent) {
            this.agents[agent.name] = agent;
            this.addToTeam(agent);
          }
        } catch (error) {
          logger.warn(`Failed to parse agent file ${fullPath}:`, error);
        }
      }
    }
  }

  /**
   * Simple YAML frontmatter parser
   */
  private parseSimpleYaml(yamlStr: string): Record<string, string> {
    const result: Record<string, string> = {};
    const lines = yamlStr.split('\n');

    let currentKey = '';
    let currentValue = '';
    let inMultiline = false;

    for (const line of lines) {
      // Check for key: value pattern
      const match = line.match(/^(\w+):\s*(.*)/);

      if (match) {
        // Save previous key-value if in multiline
        if (inMultiline && currentKey) {
          result[currentKey] = currentValue.trim();
        }

        currentKey = match[1];
        const value = match[2];

        // Check if it's a multiline value (starts with |)
        if (value.trim() === '|') {
          inMultiline = true;
          currentValue = '';
        } else {
          inMultiline = false;
          result[currentKey] = value.trim();
        }
      } else if (inMultiline && line.startsWith('  ')) {
        // Continuation of multiline value
        currentValue += line.trim() + ' ';
      }
    }

    // Save last multiline value
    if (inMultiline && currentKey) {
      result[currentKey] = currentValue.trim();
    }

    return result;
  }

  /**
   * Parse agent definition from markdown file
   */
  private parseAgentFile(filePath: string, baseDir: string): AgentDefinition | null {
    const content = fs.readFileSync(filePath, 'utf-8');

    // Extract frontmatter
    const frontmatterMatch = content.match(/^---\s*\n([\s\S]*?)\n---\s*\n/);
    if (!frontmatterMatch) {
      return null;
    }

    const frontmatter = this.parseSimpleYaml(frontmatterMatch[1]);

    // Extract markdown content
    const mdContent = content.slice(frontmatterMatch[0].length);

    // Determine team and role from path
    const relPath = path.relative(baseDir, filePath);
    const pathParts = relPath.split(path.sep);
    const team = pathParts.length > 1 ? pathParts[0] : 'general';
    const role = path.basename(filePath, '.md');

    // Parse tools
    const toolsRaw = frontmatter.tools;
    const tools = toolsRaw
      ? toolsRaw.split(',').map(t => t.trim())
      : [];

    return {
      name: frontmatter.name || `${team}/${role}`,
      description: frontmatter.description || '',
      tools,
      model: frontmatter.model || 'sonnet',
      skills: frontmatter.skills || '',
      permission_mode: frontmatter.permissionMode || 'default',
      content: mdContent,
      team,
      role
    };
  }

  /**
   * Add agent to team structure
   */
  private addToTeam(agent: AgentDefinition): void {
    const teamName = agent.team;

    if (!this.teams[teamName]) {
      this.teams[teamName] = {
        name: teamName,
        description: `${teamName.charAt(0).toUpperCase()}${teamName.slice(1)} Team`,
        leader: null,
        members: []
      };
    }

    if (agent.role === 'leader') {
      this.teams[teamName].leader = agent;
    } else {
      this.teams[teamName].members.push(agent);
    }
  }

  /**
   * Get agent by name
   */
  getAgent(name: string): AgentDefinition | null {
    return this.agents[name] || null;
  }

  /**
   * Get all teams
   */
  getTeams(): Record<string, TeamInfo> {
    return this.teams;
  }

  /**
   * Classify task as coding/non-coding
   */
  classifyTask(request: string): RoutingResult {
    const requestLower = request.toLowerCase();

    // Count keyword matches
    let codingScore = 0;
    let nonCodingScore = 0;
    const codingMatched: string[] = [];
    const nonCodingMatched: string[] = [];

    for (const kw of CODING_KEYWORDS) {
      const regex = new RegExp(`\\b${this.escapeRegex(kw)}\\b`, 'i');
      if (regex.test(request)) {
        codingScore++;
        codingMatched.push(kw);
      }
    }

    for (const kw of NON_CODING_KEYWORDS) {
      const regex = new RegExp(`\\b${this.escapeRegex(kw)}\\b`, 'i');
      if (regex.test(request)) {
        nonCodingScore++;
        nonCodingMatched.push(kw);
      }
    }

    // Determine task type
    const total = codingScore + nonCodingScore;
    let taskType: TaskType;
    let keywordsMatched: string[];

    if (codingScore > nonCodingScore) {
      taskType = 'coding';
      keywordsMatched = codingMatched;
    } else if (nonCodingScore > codingScore) {
      taskType = 'non_coding';
      keywordsMatched = nonCodingMatched;
    } else {
      taskType = total > 0 ? 'mixed' : 'non_coding';
      keywordsMatched = [...codingMatched, ...nonCodingMatched];
    }

    // Calculate confidence
    const confidence = Math.abs(codingScore - nonCodingScore) / Math.max(total, 1);

    return {
      task_type: taskType,
      target: '',
      confidence,
      keywords_matched: keywordsMatched
    };
  }

  /**
   * Route task to appropriate team/system
   */
  routeTask(request: string): RoutingResult {
    const result = this.classifyTask(request);

    if (result.task_type === 'coding') {
      result.target = 'auto-claude';
    } else if (result.task_type === 'non_coding') {
      result.target = this.getTargetTeam(request);
    } else {
      // Mixed defaults to coding
      result.target = 'auto-claude';
    }

    return result;
  }

  /**
   * Get target team for non-coding task
   */
  private getTargetTeam(request: string): string {
    const requestLower = request.toLowerCase();
    const teamScores: Record<string, number> = {};

    for (const [team, keywords] of Object.entries(TEAM_KEYWORDS)) {
      const score = keywords.filter(kw => requestLower.includes(kw.toLowerCase())).length;
      if (score > 0) {
        teamScores[team] = score;
      }
    }

    if (Object.keys(teamScores).length > 0) {
      const bestTeam = Object.entries(teamScores).sort((a, b) => b[1] - a[1])[0][0];
      return bestTeam;
    }

    return 'planning/leader';
  }

  /**
   * Escape regex special characters
   */
  private escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
}
