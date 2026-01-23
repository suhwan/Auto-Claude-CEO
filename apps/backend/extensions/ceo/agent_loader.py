"""
CEO Agent Loader - Load agent definitions from .claude/agents/
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional

from .models import AgentDefinition, TeamInfo


class AgentLoader:
    """Loads CEO agent definitions from .claude/agents/ directory"""

    def __init__(self, agents_dir: Optional[str] = None):
        """
        Initialize agent loader

        Args:
            agents_dir: Path to agents directory. If None, uses default location.
        """
        self.agents_dir = agents_dir
        self._agents: Dict[str, AgentDefinition] = {}
        self._teams: Dict[str, TeamInfo] = {}

    def _find_agents_dir(self, project_path: str) -> Optional[str]:
        """Find agents directory in project"""
        candidates = [
            os.path.join(project_path, '.claude', 'agents'),
            os.path.join(project_path, 'ceo-agents'),
            self.agents_dir
        ]

        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate

        return None

    def load_agents(self, project_path: str) -> Dict[str, AgentDefinition]:
        """
        Load all agent definitions from project

        Args:
            project_path: Path to project root

        Returns:
            Dictionary of agent_name -> AgentDefinition
        """
        agents_dir = self._find_agents_dir(project_path)
        if not agents_dir:
            return {}

        self._agents = {}
        self._teams = {}

        # Walk through agents directory
        for root, dirs, files in os.walk(agents_dir):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    try:
                        agent = self._parse_agent_file(file_path, agents_dir)
                        if agent:
                            self._agents[agent.name] = agent
                            self._add_to_team(agent)
                    except Exception as e:
                        print(f"Error parsing agent file {file_path}: {e}")

        return self._agents

    def _parse_agent_file(self, file_path: str, base_dir: str) -> Optional[AgentDefinition]:
        """
        Parse agent definition from markdown file

        Args:
            file_path: Path to agent file
            base_dir: Base agents directory

        Returns:
            AgentDefinition or None
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not frontmatter_match:
            return None

        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
        except yaml.YAMLError:
            return None

        if not isinstance(frontmatter, dict):
            return None

        # Extract markdown content (after frontmatter)
        md_content = content[frontmatter_match.end():]

        # Determine team and role from path
        rel_path = os.path.relpath(file_path, base_dir)
        path_parts = Path(rel_path).parts
        team = path_parts[0] if len(path_parts) > 1 else 'general'
        role = Path(file_path).stem

        # Parse tools list
        tools_raw = frontmatter.get('tools', '')
        if isinstance(tools_raw, str):
            tools = [t.strip() for t in tools_raw.split(',')]
        else:
            tools = tools_raw or []

        return AgentDefinition(
            name=frontmatter.get('name', f'{team}/{role}'),
            description=frontmatter.get('description', ''),
            tools=tools,
            model=frontmatter.get('model', 'sonnet'),
            skills=frontmatter.get('skills', ''),
            permission_mode=frontmatter.get('permissionMode', 'default'),
            content=md_content,
            team=team,
            role=role
        )

    def _add_to_team(self, agent: AgentDefinition):
        """Add agent to team structure"""
        team_name = agent.team

        if team_name not in self._teams:
            self._teams[team_name] = TeamInfo(
                name=team_name,
                description=f"{team_name.title()} Team"
            )

        if agent.role == 'leader':
            self._teams[team_name].leader = agent
        else:
            self._teams[team_name].members.append(agent)

    def get_agent(self, name: str) -> Optional[AgentDefinition]:
        """Get agent by name"""
        return self._agents.get(name)

    def get_team(self, team_name: str) -> Optional[TeamInfo]:
        """Get team by name"""
        return self._teams.get(team_name)

    def get_all_teams(self) -> Dict[str, TeamInfo]:
        """Get all teams"""
        return self._teams

    def get_all_agents(self) -> Dict[str, AgentDefinition]:
        """Get all agents"""
        return self._agents

    def get_team_leaders(self) -> List[AgentDefinition]:
        """Get all team leaders"""
        return [team.leader for team in self._teams.values() if team.leader]

    def to_dict(self) -> dict:
        """Convert loaded agents to dictionary"""
        return {
            'agents': {k: v.to_dict() for k, v in self._agents.items()},
            'teams': {k: v.to_dict() for k, v in self._teams.items()}
        }
