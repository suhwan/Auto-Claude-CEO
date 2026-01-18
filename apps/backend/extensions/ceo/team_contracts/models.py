"""
Team Contract Models
====================

Base data classes for team contracts (shared contracts between teams).
Contracts define standardized interfaces for API specs, UI component specs,
and data model specs to ensure consistency in cross-team collaboration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ContractType(Enum):
    """
    Contract types.

    Defines the type of interface being contracted:
    - API: REST/GraphQL API endpoints
    - UI: UI component props, events, slots
    - DATA: Data model/schema definitions
    - EVENT: Event/message contracts
    - CONFIG: Configuration schema contracts
    """
    API = "api"
    UI = "ui"
    DATA = "data"
    EVENT = "event"
    CONFIG = "config"


class ContractStatus(Enum):
    """
    Contract lifecycle status.

    - DRAFT: Initial draft, not yet proposed
    - PROPOSED: Proposed for review
    - APPROVED: Approved and active
    - DEPRECATED: Scheduled for retirement
    - RETIRED: No longer in use
    """
    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@dataclass
class ContractVersion:
    """
    Semantic version for contracts.

    Follows semantic versioning (major.minor.patch):
    - Major: Breaking changes
    - Minor: Backward-compatible additions
    - Patch: Backward-compatible fixes

    Attributes:
        major: Major version number
        minor: Minor version number
        patch: Patch version number
    """
    major: int = 1
    minor: int = 0
    patch: int = 0

    def __str__(self) -> str:
        """Return version string in 'major.minor.patch' format."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_compatible_with(self, other: 'ContractVersion') -> bool:
        """
        Check compatibility with another version.

        Versions are compatible if they share the same major version.

        Args:
            other: Another ContractVersion to compare

        Returns:
            True if compatible (same major version)
        """
        return self.major == other.major

    def bump_major(self) -> 'ContractVersion':
        """Return a new version with major incremented."""
        return ContractVersion(self.major + 1, 0, 0)

    def bump_minor(self) -> 'ContractVersion':
        """Return a new version with minor incremented."""
        return ContractVersion(self.major, self.minor + 1, 0)

    def bump_patch(self) -> 'ContractVersion':
        """Return a new version with patch incremented."""
        return ContractVersion(self.major, self.minor, self.patch + 1)

    @classmethod
    def from_string(cls, version_str: str) -> 'ContractVersion':
        """
        Parse version from string.

        Args:
            version_str: Version string like "1.2.3"

        Returns:
            ContractVersion instance
        """
        parts = version_str.split('.')
        return cls(
            major=int(parts[0]) if len(parts) > 0 else 1,
            minor=int(parts[1]) if len(parts) > 1 else 0,
            patch=int(parts[2]) if len(parts) > 2 else 0,
        )


@dataclass
class ContractOwner:
    """
    Contract owner information.

    Identifies the team responsible for maintaining the contract.

    Attributes:
        team_id: Unique identifier for the team
        team_name: Human-readable team name
        contact: Optional contact information (email, slack, etc.)
    """
    team_id: str
    team_name: str
    contact: Optional[str] = None


@dataclass
class ContractConsumer:
    """
    Contract consumer information.

    Tracks teams that consume/depend on a contract.

    Attributes:
        team_id: Unique identifier for the consuming team
        team_name: Human-readable team name
        version_used: Version of the contract being used
        registered_at: When the consumer registered
    """
    team_id: str
    team_name: str
    version_used: ContractVersion = field(default_factory=ContractVersion)
    registered_at: datetime = field(default_factory=datetime.now)


@dataclass
class Contract:
    """
    Base contract for team interfaces.

    Represents a shared contract between teams defining an interface
    (API, UI component, data model, etc.).

    Attributes:
        id: Unique contract identifier
        name: Human-readable contract name
        contract_type: Type of contract (API, UI, DATA, etc.)
        version: Current version
        status: Lifecycle status
        owner: Team owning the contract
        consumers: List of teams consuming the contract
        schema: JSON Schema definition (structure depends on contract_type)
        description: Detailed description of the contract
        tags: Tags for categorization and search
        created_at: Creation timestamp
        updated_at: Last update timestamp
        changelog: Version history with changes
        depends_on: List of contract IDs this contract depends on
    """
    id: str
    name: str
    contract_type: ContractType
    version: ContractVersion
    status: ContractStatus

    # Ownership and consumers
    owner: ContractOwner
    consumers: List[ContractConsumer] = field(default_factory=list)

    # Schema definition (JSON Schema format)
    # Structure varies by contract_type:
    # - API: { endpoints: [...], request_schema: {...}, response_schema: {...} }
    # - UI: { props: {...}, events: [...], slots: [...] }
    # - DATA: { properties: {...}, required: [...] }
    schema: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    description: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Version history
    # [{ version: "1.0.0", changes: [...], date: "...", breaking: false }]
    changelog: List[Dict[str, Any]] = field(default_factory=list)

    # Dependencies on other contracts
    depends_on: List[str] = field(default_factory=list)

    def add_consumer(self, consumer: ContractConsumer) -> None:
        """
        Add a consumer to this contract.

        Args:
            consumer: ContractConsumer to add
        """
        self.consumers.append(consumer)

    def remove_consumer(self, team_id: str) -> bool:
        """
        Remove a consumer by team ID.

        Args:
            team_id: ID of the team to remove

        Returns:
            True if consumer was removed, False if not found
        """
        original_count = len(self.consumers)
        self.consumers = [c for c in self.consumers if c.team_id != team_id]
        return len(self.consumers) < original_count

    def add_changelog_entry(
        self,
        version: ContractVersion,
        changes: List[str],
        breaking: bool = False
    ) -> None:
        """
        Add a changelog entry.

        Args:
            version: Version for this entry
            changes: List of change descriptions
            breaking: Whether this includes breaking changes
        """
        self.changelog.append({
            'version': str(version),
            'changes': changes,
            'date': datetime.now().isoformat(),
            'breaking': breaking,
        })

    def is_deprecated(self) -> bool:
        """Check if contract is deprecated or retired."""
        return self.status in (ContractStatus.DEPRECATED, ContractStatus.RETIRED)

    def is_active(self) -> bool:
        """Check if contract is approved and active."""
        return self.status == ContractStatus.APPROVED
