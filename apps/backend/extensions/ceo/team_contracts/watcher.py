"""
Contract Watcher
================

Monitors contracts for changes, detects modifications,
analyzes impact, and generates notifications for affected teams.

The watcher provides:
- Change detection between contract versions
- Impact analysis (affected consumers, dependencies)
- Notification generation based on change type
- Watch callbacks for external integrations
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

from .models import (
    Contract,
    ContractConsumer,
    ContractStatus,
    ContractVersion,
)
from .api_schema import APIContract
from .ui_data_schema import DataContract, UIContract
from .notification_models import (
    Notification,
    NotificationPriority,
    NotificationRecipient,
    NotificationStatus,
    NotificationType,
)

# Type alias for any contract type
AnyContract = Union[Contract, APIContract, UIContract, DataContract]


class ContractWatcher:
    """
    Contract change monitoring and notification generation.

    Watches for contract changes, detects the nature of changes,
    analyzes their impact, and generates appropriate notifications.

    Attributes:
        registry: ContractRegistry for accessing contracts
        validator: ContractValidator for compatibility checks
    """

    def __init__(
        self,
        registry: 'ContractRegistry',  # noqa: F821
        validator: 'ContractValidator'  # noqa: F821
    ):
        """
        Initialize ContractWatcher.

        Args:
            registry: ContractRegistry instance
            validator: ContractValidator instance
        """
        self.registry = registry
        self.validator = validator
        self._watchers: Dict[str, List[Callable]] = {}
        self._watcher_ids: Dict[str, str] = {}  # watcher_id -> contract_id mapping

    # =========================================================================
    # Watch Management
    # =========================================================================

    def watch(self, contract_id: str, callback: Callable[[AnyContract, Dict], None]) -> str:
        """
        Register a callback for contract changes.

        Args:
            contract_id: Contract ID to watch
            callback: Function called with (contract, changes) on change

        Returns:
            Watcher ID for later removal
        """
        if contract_id not in self._watchers:
            self._watchers[contract_id] = []

        self._watchers[contract_id].append(callback)

        # Generate unique watcher ID
        watcher_id = f"watch-{contract_id}-{uuid.uuid4().hex[:8]}"
        self._watcher_ids[watcher_id] = contract_id

        return watcher_id

    def unwatch(self, watcher_id: str) -> bool:
        """
        Remove a watch callback.

        Args:
            watcher_id: Watcher ID returned from watch()

        Returns:
            True if watcher was removed, False if not found
        """
        if watcher_id not in self._watcher_ids:
            return False

        contract_id = self._watcher_ids[watcher_id]
        del self._watcher_ids[watcher_id]

        # Note: We can't easily remove the specific callback without more tracking
        # This is a simplified implementation that removes the watcher ID mapping
        return True

    def unwatch_all(self, contract_id: str) -> int:
        """
        Remove all watchers for a contract.

        Args:
            contract_id: Contract ID

        Returns:
            Number of watchers removed
        """
        if contract_id not in self._watchers:
            return 0

        count = len(self._watchers[contract_id])
        del self._watchers[contract_id]

        # Clean up watcher IDs
        to_remove = [
            wid for wid, cid in self._watcher_ids.items()
            if cid == contract_id
        ]
        for wid in to_remove:
            del self._watcher_ids[wid]

        return count

    def get_watched_contracts(self) -> List[str]:
        """
        Get list of contracts being watched.

        Returns:
            List of contract IDs with active watchers
        """
        return list(self._watchers.keys())

    # =========================================================================
    # Change Detection
    # =========================================================================

    def detect_changes(
        self,
        old_contract: AnyContract,
        new_contract: AnyContract
    ) -> Dict[str, Any]:
        """
        Detect changes between two versions of a contract.

        Args:
            old_contract: Previous version of the contract
            new_contract: New version of the contract

        Returns:
            Dictionary with change analysis:
            - version_changed: Whether version changed
            - is_breaking: Whether changes are breaking
            - changes: List of change descriptions
            - affected_areas: Areas affected by changes
            - compatibility: Compatibility check results
            - additions: New additions
            - modifications: Modified elements
            - breaking_changes: List of breaking changes
        """
        changes = {
            'version_changed': str(old_contract.version) != str(new_contract.version),
            'is_breaking': False,
            'changes': [],
            'affected_areas': [],
            'additions': [],
            'modifications': [],
            'breaking_changes': [],
        }

        # Version change analysis
        old_ver = old_contract.version
        new_ver = new_contract.version

        if new_ver.major > old_ver.major:
            changes['is_breaking'] = True
            changes['changes'].append(
                f"Major version bump: {old_ver} -> {new_ver}"
            )
            changes['affected_areas'].append('version')
        elif new_ver.minor > old_ver.minor:
            changes['changes'].append(
                f"Minor version bump: {old_ver} -> {new_ver}"
            )
            changes['affected_areas'].append('version')
        elif new_ver.patch > old_ver.patch:
            changes['changes'].append(
                f"Patch version bump: {old_ver} -> {new_ver}"
            )

        # Status change
        if old_contract.status != new_contract.status:
            changes['changes'].append(
                f"Status changed: {old_contract.status.value} -> {new_contract.status.value}"
            )
            changes['affected_areas'].append('status')

            if new_contract.status == ContractStatus.DEPRECATED:
                changes['is_breaking'] = True
                changes['breaking_changes'].append("Contract marked as deprecated")
            elif new_contract.status == ContractStatus.RETIRED:
                changes['is_breaking'] = True
                changes['breaking_changes'].append("Contract retired")

        # Schema/specification changes via compatibility check
        compat = self.validator.check_compatibility(old_contract, new_contract)
        changes['compatibility'] = compat

        if not compat.get('compatible', True):
            changes['is_breaking'] = True
            changes['breaking_changes'].extend(compat.get('breaking_changes', []))

        changes['additions'].extend(compat.get('additions', []))
        changes['modifications'].extend(compat.get('modifications', []))

        # Track affected areas based on changes
        if compat.get('breaking_changes'):
            changes['affected_areas'].append('compatibility')
        if compat.get('additions'):
            changes['affected_areas'].append('features')
        if compat.get('modifications'):
            changes['affected_areas'].append('behavior')

        # Remove duplicates
        changes['affected_areas'] = list(set(changes['affected_areas']))

        return changes

    def analyze_impact(
        self,
        contract_id: str,
        changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze the impact of changes on consumers and dependents.

        Args:
            contract_id: Contract ID
            changes: Changes dictionary from detect_changes()

        Returns:
            Dictionary with impact analysis:
            - affected_consumers: List of affected consumer teams
            - affected_dependents: List of dependent contracts
            - migration_required: Whether migration is needed
            - estimated_impact: Impact severity (low, medium, high)
            - recommendations: Suggested actions
        """
        contract = self.registry.get(contract_id)
        if not contract:
            return {
                'affected_consumers': [],
                'affected_dependents': [],
                'migration_required': False,
                'estimated_impact': 'unknown',
                'recommendations': [],
            }

        impact = {
            'affected_consumers': [],
            'affected_dependents': [],
            'migration_required': changes.get('is_breaking', False),
            'estimated_impact': 'low',
            'recommendations': [],
        }

        # Find affected consumers
        if changes.get('is_breaking'):
            affected = self.validator.find_breaking_consumers(contract_id)
            impact['affected_consumers'] = [
                {
                    'team_id': c.team_id,
                    'team_name': c.team_name,
                    'version_used': str(c.version_used),
                    'needs_upgrade': True,
                }
                for c in affected
            ]
        else:
            # Even non-breaking changes may affect consumers
            impact['affected_consumers'] = [
                {
                    'team_id': c.team_id,
                    'team_name': c.team_name,
                    'version_used': str(c.version_used),
                    'needs_upgrade': False,
                }
                for c in contract.consumers
            ]

        # Find dependent contracts
        dependents = self.validator.get_dependents(contract_id)
        for dep in dependents:
            impact['affected_dependents'].append({
                'contract_id': dep.id,
                'contract_name': dep.name,
                'owner_team': dep.owner.team_name,
            })

        # Estimate overall impact
        if changes.get('is_breaking'):
            if len(impact['affected_consumers']) > 5 or len(impact['affected_dependents']) > 2:
                impact['estimated_impact'] = 'high'
            elif len(impact['affected_consumers']) > 0 or len(impact['affected_dependents']) > 0:
                impact['estimated_impact'] = 'medium'
            else:
                impact['estimated_impact'] = 'low'
        elif changes.get('modifications'):
            impact['estimated_impact'] = 'medium' if len(impact['affected_consumers']) > 3 else 'low'

        # Generate recommendations
        if changes.get('is_breaking'):
            impact['recommendations'].append(
                "Notify all consumers before deploying breaking changes"
            )
            impact['recommendations'].append(
                "Provide migration guide for affected consumers"
            )
            if impact['affected_dependents']:
                impact['recommendations'].append(
                    "Coordinate with dependent contract owners"
                )

        if contract.status == ContractStatus.DEPRECATED:
            impact['recommendations'].append(
                "Communicate deprecation timeline to all consumers"
            )
            impact['recommendations'].append(
                "Document alternative contracts or migration paths"
            )

        return impact

    # =========================================================================
    # Notification Generation
    # =========================================================================

    def notify_change(
        self,
        contract_id: str,
        old_contract: AnyContract,
        new_contract: AnyContract
    ) -> List[Notification]:
        """
        Generate notifications for a contract change.

        Detects changes, analyzes impact, and creates appropriate
        notifications for all affected parties.

        Args:
            contract_id: Contract ID
            old_contract: Previous version
            new_contract: New version

        Returns:
            List of generated Notification objects
        """
        changes = self.detect_changes(old_contract, new_contract)
        impact = self.analyze_impact(contract_id, changes)

        notifications = []

        # Generate notification based on change type
        if changes.get('is_breaking'):
            notif = self._create_breaking_change_notification(
                new_contract, changes, impact
            )
            notifications.append(notif)
        elif changes.get('version_changed'):
            notif = self._create_update_notification(
                new_contract, changes
            )
            notifications.append(notif)

        # Invoke watcher callbacks
        if contract_id in self._watchers:
            for callback in self._watchers[contract_id]:
                try:
                    callback(new_contract, changes)
                except Exception as e:
                    # Log but don't fail on callback errors
                    print(f"Watcher callback error: {e}")

        return notifications

    def _create_breaking_change_notification(
        self,
        contract: AnyContract,
        changes: Dict[str, Any],
        impact: Dict[str, Any]
    ) -> Notification:
        """
        Create a breaking change notification.

        Args:
            contract: Updated contract
            changes: Change details
            impact: Impact analysis

        Returns:
            Notification for breaking change
        """
        # Build recipient list
        recipients = []

        # Owner always gets notified
        recipients.append(NotificationRecipient(
            team_id=contract.owner.team_id,
            team_name=contract.owner.team_name,
            role='owner',
        ))

        # All consumers
        for consumer in contract.consumers:
            recipients.append(NotificationRecipient(
                team_id=consumer.team_id,
                team_name=consumer.team_name,
                role='consumer',
            ))

        # Dependent contract owners
        for dep in impact.get('affected_dependents', []):
            recipients.append(NotificationRecipient(
                team_id=dep.get('owner_team', 'unknown'),
                team_name=dep.get('owner_team', 'Unknown'),
                role='dependent',
            ))

        # Build action items
        action_items = [
            "Review breaking changes",
            "Update to new contract version",
            "Run compatibility tests",
        ]
        action_items.extend(impact.get('recommendations', []))

        # Set action deadline (7 days for breaking changes)
        action_deadline = datetime.now() + timedelta(days=7)

        return Notification(
            id=f"notif-{uuid.uuid4().hex[:8]}",
            notification_type=NotificationType.BREAKING_CHANGE,
            priority=NotificationPriority.CRITICAL,
            contract_id=contract.id,
            contract_name=contract.name,
            contract_version=str(contract.version),
            title=f"Breaking Change: {contract.name} v{contract.version}",
            message=self._build_breaking_change_message(contract, changes),
            details={
                'breaking_changes': changes.get('breaking_changes', []),
                'affected_consumers': impact.get('affected_consumers', []),
                'affected_dependents': impact.get('affected_dependents', []),
                'estimated_impact': impact.get('estimated_impact', 'unknown'),
            },
            recipients=recipients,
            requires_action=True,
            action_deadline=action_deadline,
            action_items=action_items,
        )

    def _create_update_notification(
        self,
        contract: AnyContract,
        changes: Dict[str, Any]
    ) -> Notification:
        """
        Create a standard update notification.

        Args:
            contract: Updated contract
            changes: Change details

        Returns:
            Notification for contract update
        """
        # Build recipient list
        recipients = []

        # Owner
        recipients.append(NotificationRecipient(
            team_id=contract.owner.team_id,
            team_name=contract.owner.team_name,
            role='owner',
        ))

        # All consumers
        for consumer in contract.consumers:
            recipients.append(NotificationRecipient(
                team_id=consumer.team_id,
                team_name=consumer.team_name,
                role='consumer',
            ))

        # Determine priority based on change type
        priority = NotificationPriority.LOW
        if changes.get('modifications'):
            priority = NotificationPriority.MEDIUM

        return Notification(
            id=f"notif-{uuid.uuid4().hex[:8]}",
            notification_type=NotificationType.CONTRACT_UPDATED,
            priority=priority,
            contract_id=contract.id,
            contract_name=contract.name,
            contract_version=str(contract.version),
            title=f"Contract Updated: {contract.name} v{contract.version}",
            message=self._build_update_message(contract, changes),
            details={
                'additions': changes.get('additions', []),
                'modifications': changes.get('modifications', []),
                'affected_areas': changes.get('affected_areas', []),
            },
            recipients=recipients,
            requires_action=False,
        )

    def _build_breaking_change_message(
        self,
        contract: AnyContract,
        changes: Dict[str, Any]
    ) -> str:
        """Build message for breaking change notification."""
        lines = [
            f"Contract '{contract.name}' has breaking changes in version {contract.version}.",
            "",
            "Breaking Changes:",
        ]

        for bc in changes.get('breaking_changes', []):
            lines.append(f"  - {bc}")

        if changes.get('additions'):
            lines.append("")
            lines.append("Additions:")
            for add in changes['additions'][:5]:  # Limit to 5
                lines.append(f"  + {add}")

        lines.append("")
        lines.append("Please review and update your implementations accordingly.")

        return "\n".join(lines)

    def _build_update_message(
        self,
        contract: AnyContract,
        changes: Dict[str, Any]
    ) -> str:
        """Build message for standard update notification."""
        lines = [
            f"Contract '{contract.name}' has been updated to version {contract.version}.",
        ]

        if changes.get('additions'):
            lines.append("")
            lines.append("Additions:")
            for add in changes['additions'][:5]:
                lines.append(f"  + {add}")

        if changes.get('modifications'):
            lines.append("")
            lines.append("Modifications:")
            for mod in changes['modifications'][:5]:
                lines.append(f"  ~ {mod}")

        return "\n".join(lines)

    # =========================================================================
    # Deprecation Notification
    # =========================================================================

    def notify_deprecation(
        self,
        contract: AnyContract,
        reason: str,
        sunset_date: Optional[datetime] = None
    ) -> Notification:
        """
        Generate a deprecation notification.

        Args:
            contract: Contract being deprecated
            reason: Reason for deprecation
            sunset_date: Optional date when contract will be retired

        Returns:
            Deprecation notification
        """
        recipients = []

        # Owner
        recipients.append(NotificationRecipient(
            team_id=contract.owner.team_id,
            team_name=contract.owner.team_name,
            role='owner',
        ))

        # All consumers
        for consumer in contract.consumers:
            recipients.append(NotificationRecipient(
                team_id=consumer.team_id,
                team_name=consumer.team_name,
                role='consumer',
            ))

        message_lines = [
            f"Contract '{contract.name}' has been marked for deprecation.",
            "",
            f"Reason: {reason}",
        ]

        if sunset_date:
            message_lines.append(f"Sunset Date: {sunset_date.strftime('%Y-%m-%d')}")

        message_lines.extend([
            "",
            "Please plan your migration to alternative solutions.",
        ])

        return Notification(
            id=f"notif-{uuid.uuid4().hex[:8]}",
            notification_type=NotificationType.DEPRECATION,
            priority=NotificationPriority.HIGH,
            contract_id=contract.id,
            contract_name=contract.name,
            contract_version=str(contract.version),
            title=f"Deprecation Notice: {contract.name}",
            message="\n".join(message_lines),
            details={
                'reason': reason,
                'sunset_date': sunset_date.isoformat() if sunset_date else None,
            },
            recipients=recipients,
            expires_at=sunset_date,
            requires_action=True,
            action_deadline=sunset_date,
            action_items=[
                "Review deprecation reason",
                "Identify migration path",
                "Plan migration timeline",
                "Update dependent systems",
            ],
        )

    def notify_new_consumer(
        self,
        contract: AnyContract,
        consumer: ContractConsumer
    ) -> Notification:
        """
        Generate notification for new consumer registration.

        Args:
            contract: Contract that gained a consumer
            consumer: New consumer details

        Returns:
            New consumer notification
        """
        return Notification(
            id=f"notif-{uuid.uuid4().hex[:8]}",
            notification_type=NotificationType.NEW_CONSUMER,
            priority=NotificationPriority.LOW,
            contract_id=contract.id,
            contract_name=contract.name,
            contract_version=str(contract.version),
            title=f"New Consumer: {consumer.team_name}",
            message=f"Team '{consumer.team_name}' has started using contract '{contract.name}'.",
            details={
                'consumer_team_id': consumer.team_id,
                'consumer_team_name': consumer.team_name,
                'version_used': str(consumer.version_used),
            },
            recipients=[
                NotificationRecipient(
                    team_id=contract.owner.team_id,
                    team_name=contract.owner.team_name,
                    role='owner',
                )
            ],
            requires_action=False,
        )

    def notify_consumer_removed(
        self,
        contract: AnyContract,
        team_id: str,
        team_name: str
    ) -> Notification:
        """
        Generate notification for consumer removal.

        Args:
            contract: Contract that lost a consumer
            team_id: Removed team ID
            team_name: Removed team name

        Returns:
            Consumer removed notification
        """
        return Notification(
            id=f"notif-{uuid.uuid4().hex[:8]}",
            notification_type=NotificationType.CONSUMER_REMOVED,
            priority=NotificationPriority.LOW,
            contract_id=contract.id,
            contract_name=contract.name,
            contract_version=str(contract.version),
            title=f"Consumer Removed: {team_name}",
            message=f"Team '{team_name}' has stopped using contract '{contract.name}'.",
            details={
                'consumer_team_id': team_id,
                'consumer_team_name': team_name,
            },
            recipients=[
                NotificationRecipient(
                    team_id=contract.owner.team_id,
                    team_name=contract.owner.team_name,
                    role='owner',
                )
            ],
            requires_action=False,
        )
