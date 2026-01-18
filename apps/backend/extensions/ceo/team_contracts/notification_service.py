"""
Notification Service
====================

Manages notification storage, delivery, and retrieval for the
contract change notification system.

Provides:
- Notification sending and delivery tracking
- Query and filtering capabilities
- Read/acknowledge status management
- Subscription management for teams
- Notification statistics

Storage location: `.planning/contracts/notifications/`
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .models import Contract
from .api_schema import APIContract
from .ui_data_schema import DataContract, UIContract
from .notification_models import (
    Notification,
    NotificationPriority,
    NotificationRecipient,
    NotificationStatus,
    NotificationSubscription,
    NotificationType,
)

# Type alias for any contract type
AnyContract = Union[Contract, APIContract, UIContract, DataContract]


class NotificationService:
    """
    Notification service for contract change notifications.

    Handles notification storage, delivery tracking, queries,
    and subscription management.

    Attributes:
        project_path: Path to the project root
        registry: ContractRegistry for contract lookups
        notifications_dir: Path to notifications storage
    """

    # Storage configuration
    NOTIFICATIONS_FILE = "notifications.json"
    SUBSCRIPTIONS_FILE = "subscriptions.json"

    def __init__(self, project_path: str, registry: 'ContractRegistry'):  # noqa: F821
        """
        Initialize NotificationService.

        Args:
            project_path: Path to the project root
            registry: ContractRegistry instance
        """
        self.project_path = Path(project_path)
        self.registry = registry
        self.notifications_dir = self.project_path / ".planning" / "contracts" / "notifications"
        self.notifications_dir.mkdir(parents=True, exist_ok=True)

        self._notifications: List[Notification] = []
        self._subscriptions: Dict[str, List[NotificationSubscription]] = {}

        self._load()

    # =========================================================================
    # Persistence
    # =========================================================================

    def _load(self) -> None:
        """Load notifications and subscriptions from files."""
        self._load_notifications()
        self._load_subscriptions()

    def _load_notifications(self) -> None:
        """Load notifications from file."""
        notifications_path = self.notifications_dir / self.NOTIFICATIONS_FILE
        if notifications_path.exists():
            try:
                with open(notifications_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._notifications = [
                    Notification.from_dict(n) for n in data.get('notifications', [])
                ]
            except (json.JSONDecodeError, IOError, KeyError) as e:
                print(f"Error loading notifications: {e}")
                self._notifications = []
        else:
            self._notifications = []

    def _load_subscriptions(self) -> None:
        """Load subscriptions from file."""
        subscriptions_path = self.notifications_dir / self.SUBSCRIPTIONS_FILE
        if subscriptions_path.exists():
            try:
                with open(subscriptions_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._subscriptions = {}
                for team_id, subs in data.get('subscriptions', {}).items():
                    self._subscriptions[team_id] = [
                        NotificationSubscription.from_dict(s) for s in subs
                    ]
            except (json.JSONDecodeError, IOError, KeyError) as e:
                print(f"Error loading subscriptions: {e}")
                self._subscriptions = {}
        else:
            self._subscriptions = {}

    def _save(self) -> None:
        """Save notifications and subscriptions to files."""
        self._save_notifications()
        self._save_subscriptions()

    def _save_notifications(self) -> None:
        """Save notifications to file."""
        notifications_path = self.notifications_dir / self.NOTIFICATIONS_FILE
        try:
            data = {
                'notifications': [n.to_dict() for n in self._notifications],
                'last_updated': datetime.now().isoformat(),
            }
            with open(notifications_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving notifications: {e}")

    def _save_subscriptions(self) -> None:
        """Save subscriptions to file."""
        subscriptions_path = self.notifications_dir / self.SUBSCRIPTIONS_FILE
        try:
            data = {
                'subscriptions': {
                    team_id: [s.to_dict() for s in subs]
                    for team_id, subs in self._subscriptions.items()
                },
                'last_updated': datetime.now().isoformat(),
            }
            with open(subscriptions_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving subscriptions: {e}")

    # =========================================================================
    # Notification Sending
    # =========================================================================

    def send(self, notification: Notification) -> bool:
        """
        Send a notification.

        Adds the notification to storage and marks recipients as sent.

        Args:
            notification: Notification to send

        Returns:
            True if notification was sent successfully
        """
        # Update recipient statuses
        now = datetime.now()
        for recipient in notification.recipients:
            # Check if recipient has subscription that blocks this notification
            if not self._should_receive(recipient.team_id, notification):
                continue

            recipient.status = NotificationStatus.SENT
            recipient.sent_at = now

        # Store notification
        self._notifications.append(notification)
        self._save_notifications()

        return True

    def send_to_team(
        self,
        team_id: str,
        notification_type: NotificationType,
        contract: AnyContract,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM
    ) -> Notification:
        """
        Send a notification to a specific team.

        Args:
            team_id: Target team ID
            notification_type: Type of notification
            contract: Related contract
            message: Notification message
            priority: Notification priority

        Returns:
            Created Notification
        """
        notif = Notification(
            id=f"notif-{uuid.uuid4().hex[:8]}",
            notification_type=notification_type,
            priority=priority,
            contract_id=contract.id,
            contract_name=contract.name,
            contract_version=str(contract.version),
            title=self._generate_title(notification_type, contract),
            message=message,
            recipients=[
                NotificationRecipient(
                    team_id=team_id,
                    team_name=team_id,  # Default to team_id if name unknown
                    role="recipient",
                )
            ],
        )

        self.send(notif)
        return notif

    def broadcast_to_consumers(
        self,
        contract: AnyContract,
        notification_type: NotificationType,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM
    ) -> Notification:
        """
        Broadcast a notification to all consumers of a contract.

        Also notifies the contract owner.

        Args:
            contract: Contract whose consumers to notify
            notification_type: Type of notification
            message: Notification message
            priority: Notification priority

        Returns:
            Created Notification
        """
        recipients = []

        # Add all consumers
        for consumer in contract.consumers:
            recipients.append(NotificationRecipient(
                team_id=consumer.team_id,
                team_name=consumer.team_name,
                role="consumer",
            ))

        # Add owner
        recipients.append(NotificationRecipient(
            team_id=contract.owner.team_id,
            team_name=contract.owner.team_name,
            role="owner",
        ))

        notif = Notification(
            id=f"notif-{uuid.uuid4().hex[:8]}",
            notification_type=notification_type,
            priority=priority,
            contract_id=contract.id,
            contract_name=contract.name,
            contract_version=str(contract.version),
            title=self._generate_title(notification_type, contract),
            message=message,
            recipients=recipients,
        )

        self.send(notif)
        return notif

    def _should_receive(self, team_id: str, notification: Notification) -> bool:
        """
        Check if a team should receive a notification based on subscriptions.

        Args:
            team_id: Team ID
            notification: Notification to check

        Returns:
            True if team should receive the notification
        """
        if team_id not in self._subscriptions:
            return True  # No subscriptions means receive all

        for sub in self._subscriptions[team_id]:
            if sub.matches(notification):
                return True

        # If team has subscriptions but none match, still send
        # (subscriptions are opt-in additions, not filters by default)
        return True

    def _generate_title(
        self,
        notification_type: NotificationType,
        contract: AnyContract
    ) -> str:
        """Generate notification title based on type."""
        titles = {
            NotificationType.CONTRACT_UPDATED: f"Contract Updated: {contract.name}",
            NotificationType.BREAKING_CHANGE: f"Breaking Change: {contract.name}",
            NotificationType.DEPRECATION: f"Deprecation Notice: {contract.name}",
            NotificationType.NEW_CONSUMER: f"New Consumer for {contract.name}",
            NotificationType.CONSUMER_REMOVED: f"Consumer Removed from {contract.name}",
            NotificationType.DEPENDENCY_CHANGED: f"Dependency Change: {contract.name}",
            NotificationType.CONTRACT_RETIRED: f"Contract Retired: {contract.name}",
        }
        return titles.get(notification_type, f"Notification: {contract.name}")

    # =========================================================================
    # Query and Filtering
    # =========================================================================

    def get_notifications(
        self,
        team_id: Optional[str] = None,
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[NotificationType] = None,
        contract_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Notification]:
        """
        Query notifications with optional filters.

        Args:
            team_id: Filter by recipient team
            status: Filter by recipient status
            notification_type: Filter by notification type
            contract_id: Filter by contract
            limit: Maximum number of results

        Returns:
            List of matching notifications (most recent first)
        """
        result = self._notifications

        if team_id:
            result = [
                n for n in result
                if any(r.team_id == team_id for r in n.recipients)
            ]

        if status:
            def has_status(notif: Notification) -> bool:
                for recipient in notif.recipients:
                    if team_id and recipient.team_id != team_id:
                        continue
                    if recipient.status == status:
                        return True
                return False

            result = [n for n in result if has_status(n)]

        if notification_type:
            result = [n for n in result if n.notification_type == notification_type]

        if contract_id:
            result = [n for n in result if n.contract_id == contract_id]

        # Sort by created_at descending (most recent first)
        result = sorted(result, key=lambda n: n.created_at, reverse=True)

        if limit:
            result = result[:limit]

        return result

    def get_unread(self, team_id: str) -> List[Notification]:
        """
        Get unread notifications for a team.

        Args:
            team_id: Team ID

        Returns:
            List of notifications with SENT status for the team
        """
        return self.get_notifications(team_id=team_id, status=NotificationStatus.SENT)

    def get_pending_actions(self, team_id: str) -> List[Notification]:
        """
        Get notifications requiring action from a team.

        Args:
            team_id: Team ID

        Returns:
            List of notifications requiring action that aren't acknowledged
        """
        result = []

        for notif in self._notifications:
            if not notif.requires_action:
                continue

            for recipient in notif.recipients:
                if recipient.team_id == team_id:
                    if recipient.status != NotificationStatus.ACKNOWLEDGED:
                        result.append(notif)
                        break

        return sorted(result, key=lambda n: n.created_at, reverse=True)

    def get_by_id(self, notification_id: str) -> Optional[Notification]:
        """
        Get a notification by ID.

        Args:
            notification_id: Notification ID

        Returns:
            Notification if found, None otherwise
        """
        for notif in self._notifications:
            if notif.id == notification_id:
                return notif
        return None

    # =========================================================================
    # Status Updates
    # =========================================================================

    def mark_read(self, notification_id: str, team_id: str) -> bool:
        """
        Mark a notification as read for a team.

        Args:
            notification_id: Notification ID
            team_id: Team ID

        Returns:
            True if status was updated
        """
        for notif in self._notifications:
            if notif.id == notification_id:
                for recipient in notif.recipients:
                    if recipient.team_id == team_id:
                        recipient.status = NotificationStatus.READ
                        recipient.read_at = datetime.now()
                        self._save_notifications()
                        return True
        return False

    def acknowledge(self, notification_id: str, team_id: str) -> bool:
        """
        Acknowledge a notification (mark action completed).

        Args:
            notification_id: Notification ID
            team_id: Team ID

        Returns:
            True if status was updated
        """
        for notif in self._notifications:
            if notif.id == notification_id:
                for recipient in notif.recipients:
                    if recipient.team_id == team_id:
                        recipient.status = NotificationStatus.ACKNOWLEDGED
                        recipient.acknowledged_at = datetime.now()
                        self._save_notifications()
                        return True
        return False

    def mark_all_read(self, team_id: str) -> int:
        """
        Mark all notifications as read for a team.

        Args:
            team_id: Team ID

        Returns:
            Number of notifications marked as read
        """
        count = 0
        now = datetime.now()

        for notif in self._notifications:
            for recipient in notif.recipients:
                if recipient.team_id == team_id:
                    if recipient.status == NotificationStatus.SENT:
                        recipient.status = NotificationStatus.READ
                        recipient.read_at = now
                        count += 1

        if count > 0:
            self._save_notifications()

        return count

    # =========================================================================
    # Subscription Management
    # =========================================================================

    def subscribe(self, subscription: NotificationSubscription) -> bool:
        """
        Add a notification subscription.

        Args:
            subscription: Subscription to add

        Returns:
            True if subscription was added
        """
        team_id = subscription.team_id

        if team_id not in self._subscriptions:
            self._subscriptions[team_id] = []

        # Check for duplicate
        for existing in self._subscriptions[team_id]:
            if existing.contract_id == subscription.contract_id:
                # Update existing subscription
                self._subscriptions[team_id].remove(existing)
                break

        self._subscriptions[team_id].append(subscription)
        self._save_subscriptions()

        return True

    def unsubscribe(
        self,
        team_id: str,
        contract_id: Optional[str] = None
    ) -> bool:
        """
        Remove a notification subscription.

        Args:
            team_id: Team ID
            contract_id: Contract ID (None to remove all)

        Returns:
            True if subscription was removed
        """
        if team_id not in self._subscriptions:
            return False

        if contract_id is None:
            # Remove all subscriptions for team
            del self._subscriptions[team_id]
        else:
            # Remove specific subscription
            self._subscriptions[team_id] = [
                s for s in self._subscriptions[team_id]
                if s.contract_id != contract_id
            ]

        self._save_subscriptions()
        return True

    def get_subscriptions(self, team_id: str) -> List[NotificationSubscription]:
        """
        Get subscriptions for a team.

        Args:
            team_id: Team ID

        Returns:
            List of NotificationSubscription objects
        """
        return self._subscriptions.get(team_id, [])

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_stats(self, team_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get notification statistics.

        Args:
            team_id: Optional team ID to filter stats

        Returns:
            Dictionary with notification statistics
        """
        notifications = self.get_notifications(team_id=team_id)

        stats = {
            'total': len(notifications),
            'unread': 0,
            'pending_actions': 0,
            'by_type': {},
            'by_priority': {},
        }

        for notif in notifications:
            # Count by type
            ntype = notif.notification_type.value
            stats['by_type'][ntype] = stats['by_type'].get(ntype, 0) + 1

            # Count by priority
            priority = notif.priority.value
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1

            # Count unread
            if team_id:
                for recipient in notif.recipients:
                    if recipient.team_id == team_id:
                        if recipient.status == NotificationStatus.SENT:
                            stats['unread'] += 1
                        break
            else:
                if any(r.status == NotificationStatus.SENT for r in notif.recipients):
                    stats['unread'] += 1

            # Count pending actions
            if notif.requires_action:
                if team_id:
                    for recipient in notif.recipients:
                        if recipient.team_id == team_id:
                            if recipient.status != NotificationStatus.ACKNOWLEDGED:
                                stats['pending_actions'] += 1
                            break
                else:
                    if any(r.status != NotificationStatus.ACKNOWLEDGED for r in notif.recipients):
                        stats['pending_actions'] += 1

        return stats

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about notification storage.

        Returns:
            Dictionary with storage statistics
        """
        total_size = 0
        if self.notifications_dir.exists():
            for file in self.notifications_dir.iterdir():
                if file.is_file():
                    total_size += file.stat().st_size

        return {
            'storage_path': str(self.notifications_dir),
            'total_notifications': len(self._notifications),
            'total_subscriptions': sum(
                len(subs) for subs in self._subscriptions.values()
            ),
            'teams_with_subscriptions': len(self._subscriptions),
            'total_size_bytes': total_size,
        }

    # =========================================================================
    # Cleanup
    # =========================================================================

    def cleanup_expired(self) -> int:
        """
        Remove expired notifications.

        Returns:
            Number of notifications removed
        """
        now = datetime.now()
        original_count = len(self._notifications)

        self._notifications = [
            n for n in self._notifications
            if n.expires_at is None or n.expires_at > now
        ]

        removed = original_count - len(self._notifications)

        if removed > 0:
            self._save_notifications()

        return removed

    def cleanup_old(self, days: int = 30) -> int:
        """
        Remove notifications older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of notifications removed
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        original_count = len(self._notifications)

        self._notifications = [
            n for n in self._notifications
            if n.created_at > cutoff
        ]

        removed = original_count - len(self._notifications)

        if removed > 0:
            self._save_notifications()

        return removed
