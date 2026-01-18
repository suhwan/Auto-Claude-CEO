"""
Notification Models
===================

Data models for the contract change notification system.
Defines notification types, priorities, statuses, and data structures
for tracking and delivering notifications to teams.

Notification storage: `.planning/contracts/notifications/`
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class NotificationType(Enum):
    """
    Notification types for contract changes.

    Types:
    - CONTRACT_UPDATED: Minor or patch version changes
    - BREAKING_CHANGE: Major version changes with breaking compatibility
    - DEPRECATION: Contract scheduled for retirement
    - NEW_CONSUMER: New team started using the contract
    - CONSUMER_REMOVED: Team stopped using the contract
    - DEPENDENCY_CHANGED: Dependent contract was modified
    - CONTRACT_RETIRED: Contract is no longer available
    """
    CONTRACT_UPDATED = "contract_updated"
    BREAKING_CHANGE = "breaking_change"
    DEPRECATION = "deprecation"
    NEW_CONSUMER = "new_consumer"
    CONSUMER_REMOVED = "consumer_removed"
    DEPENDENCY_CHANGED = "dependency_changed"
    CONTRACT_RETIRED = "contract_retired"


class NotificationPriority(Enum):
    """
    Notification priority levels.

    Levels:
    - LOW: Informational, no action required
    - MEDIUM: May require attention
    - HIGH: Requires attention soon
    - CRITICAL: Requires immediate attention
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(Enum):
    """
    Notification delivery and read status.

    Statuses:
    - PENDING: Not yet sent
    - SENT: Sent to recipient
    - READ: Read by recipient
    - ACKNOWLEDGED: Recipient confirmed awareness/action
    """
    PENDING = "pending"
    SENT = "sent"
    READ = "read"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class NotificationRecipient:
    """
    Notification recipient information.

    Tracks the delivery status for each recipient team.

    Attributes:
        team_id: Unique identifier for the team
        team_name: Human-readable team name
        role: Recipient's relationship to contract (owner, consumer, dependent)
        status: Current delivery/read status
        sent_at: When the notification was sent
        read_at: When the notification was read
        acknowledged_at: When the notification was acknowledged
    """
    team_id: str
    team_name: str
    role: str  # owner, consumer, dependent
    status: NotificationStatus = NotificationStatus.PENDING
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'team_id': self.team_id,
            'team_name': self.team_name,
            'role': self.role,
            'status': self.status.value,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationRecipient':
        """Create from dictionary."""
        return cls(
            team_id=data['team_id'],
            team_name=data['team_name'],
            role=data['role'],
            status=NotificationStatus(data.get('status', 'pending')),
            sent_at=datetime.fromisoformat(data['sent_at']) if data.get('sent_at') else None,
            read_at=datetime.fromisoformat(data['read_at']) if data.get('read_at') else None,
            acknowledged_at=datetime.fromisoformat(data['acknowledged_at']) if data.get('acknowledged_at') else None,
        )


@dataclass
class Notification:
    """
    Notification data structure.

    Represents a notification about a contract change or event,
    including the type, priority, content, and delivery tracking.

    Attributes:
        id: Unique notification identifier
        notification_type: Type of notification
        priority: Priority level
        contract_id: Related contract ID
        contract_name: Related contract name
        contract_version: Contract version at time of notification
        title: Notification title
        message: Notification message body
        details: Additional details (breaking_changes, affected_endpoints, etc.)
        recipients: List of recipient teams with delivery status
        created_at: When the notification was created
        expires_at: Optional expiration date
        requires_action: Whether recipient action is required
        action_deadline: Deadline for required action
        action_items: List of action items for recipients
    """
    id: str
    notification_type: NotificationType
    priority: NotificationPriority

    # Related contract
    contract_id: str
    contract_name: str
    contract_version: str

    # Content
    title: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    # Recipients
    recipients: List[NotificationRecipient] = field(default_factory=list)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    # Action requirements
    requires_action: bool = False
    action_deadline: Optional[datetime] = None
    action_items: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'notification_type': self.notification_type.value,
            'priority': self.priority.value,
            'contract_id': self.contract_id,
            'contract_name': self.contract_name,
            'contract_version': self.contract_version,
            'title': self.title,
            'message': self.message,
            'details': self.details,
            'recipients': [r.to_dict() for r in self.recipients],
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'requires_action': self.requires_action,
            'action_deadline': self.action_deadline.isoformat() if self.action_deadline else None,
            'action_items': self.action_items,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            notification_type=NotificationType(data['notification_type']),
            priority=NotificationPriority(data['priority']),
            contract_id=data['contract_id'],
            contract_name=data['contract_name'],
            contract_version=data['contract_version'],
            title=data['title'],
            message=data['message'],
            details=data.get('details', {}),
            recipients=[
                NotificationRecipient.from_dict(r)
                for r in data.get('recipients', [])
            ],
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            requires_action=data.get('requires_action', False),
            action_deadline=datetime.fromisoformat(data['action_deadline']) if data.get('action_deadline') else None,
            action_items=data.get('action_items', []),
        )


@dataclass
class NotificationSubscription:
    """
    Notification subscription settings.

    Allows teams to configure their notification preferences for
    specific contracts or all contracts.

    Attributes:
        team_id: Team identifier
        contract_id: Specific contract ID (None for all contracts)
        notification_types: Types to receive (empty for all types)
        min_priority: Minimum priority to receive
        enabled: Whether subscription is active
        created_at: When the subscription was created
    """
    team_id: str
    contract_id: Optional[str] = None  # None means all contracts
    notification_types: List[NotificationType] = field(default_factory=list)
    min_priority: NotificationPriority = NotificationPriority.LOW
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'team_id': self.team_id,
            'contract_id': self.contract_id,
            'notification_types': [t.value for t in self.notification_types],
            'min_priority': self.min_priority.value,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationSubscription':
        """Create from dictionary."""
        return cls(
            team_id=data['team_id'],
            contract_id=data.get('contract_id'),
            notification_types=[
                NotificationType(t) for t in data.get('notification_types', [])
            ],
            min_priority=NotificationPriority(data.get('min_priority', 'low')),
            enabled=data.get('enabled', True),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
        )

    def matches(self, notification: Notification) -> bool:
        """
        Check if a notification matches this subscription.

        Args:
            notification: Notification to check

        Returns:
            True if the notification matches subscription criteria
        """
        if not self.enabled:
            return False

        # Check contract filter
        if self.contract_id and notification.contract_id != self.contract_id:
            return False

        # Check notification type filter
        if self.notification_types and notification.notification_type not in self.notification_types:
            return False

        # Check priority
        priority_order = [NotificationPriority.LOW, NotificationPriority.MEDIUM,
                         NotificationPriority.HIGH, NotificationPriority.CRITICAL]
        if priority_order.index(notification.priority) < priority_order.index(self.min_priority):
            return False

        return True
