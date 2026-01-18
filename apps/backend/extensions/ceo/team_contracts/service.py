"""
Team Contract Service
=====================

Unified service facade for team contracts, integrating all components:
- ContractRegistry for storage
- ContractVersionManager for versioning
- ContractValidator for validation
- ContractWatcher for change monitoring
- NotificationService for notifications

Provides a high-level API for contract management with automatic
change tracking, validation, and notification handling.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .models import (
    Contract,
    ContractConsumer,
    ContractStatus,
    ContractVersion,
)
from .api_schema import APIContract
from .ui_data_schema import DataContract, UIContract
from .registry import ContractRegistry
from .version_manager import ContractVersionManager
from .validator import ContractValidator
from .watcher import ContractWatcher
from .notification_service import NotificationService
from .notification_models import (
    NotificationPriority,
    NotificationType,
)

# Type alias for any contract type
AnyContract = Union[Contract, APIContract, UIContract, DataContract]


class TeamContractService:
    """
    Unified team contract management service.

    Integrates all contract management components and provides
    a high-level API for common operations with automatic
    validation, versioning, and notification handling.

    Attributes:
        project_path: Path to the project root
        registry: Contract storage and retrieval
        validator: Contract validation
        version_manager: Version management
        watcher: Change monitoring
        notifications: Notification delivery
    """

    def __init__(self, project_path: str):
        """
        Initialize TeamContractService.

        Creates and initializes all component services.

        Args:
            project_path: Path to the project root
        """
        self.project_path = project_path

        # Initialize components
        self.registry = ContractRegistry(project_path)
        self.validator = ContractValidator(self.registry)
        self.version_manager = ContractVersionManager(self.registry)
        self.watcher = ContractWatcher(self.registry, self.validator)
        self.notifications = NotificationService(project_path, self.registry)

    # =========================================================================
    # Contract Lifecycle
    # =========================================================================

    def create_contract(self, contract: AnyContract) -> Dict[str, Any]:
        """
        Create a new contract.

        Validates the contract, checks dependencies, and registers it.

        Args:
            contract: Contract to create

        Returns:
            Dictionary with:
            - success: Whether creation succeeded
            - contract: Created contract (if successful)
            - errors: List of validation errors (if failed)
        """
        # 1. Validate contract
        errors = self.validator.validate(contract)
        if errors:
            return {
                'success': False,
                'errors': errors,
            }

        # 2. Check dependencies
        deps = self.validator.check_dependencies(contract)
        if not deps['satisfied']:
            return {
                'success': False,
                'errors': [f"Missing dependency: {d}" for d in deps['missing']],
                'warnings': deps.get('version_mismatch', []),
            }

        # 3. Register contract
        if not self.registry.register(contract):
            return {
                'success': False,
                'errors': ["Failed to register contract (may already exist)"],
            }

        return {
            'success': True,
            'contract': contract,
            'warnings': deps.get('version_mismatch', []),
        }

    def update_contract(
        self,
        contract_id: str,
        changes: Dict[str, Any],
        bump_type: str = "patch",
        changelog: str = ""
    ) -> Dict[str, Any]:
        """
        Update an existing contract.

        Validates changes, updates version, generates notifications.

        Args:
            contract_id: Contract ID to update
            changes: Dictionary of field changes
            bump_type: Version bump type (major, minor, patch)
            changelog: Description of changes

        Returns:
            Dictionary with:
            - success: Whether update succeeded
            - contract: Updated contract (if successful)
            - notifications_sent: Number of notifications sent
            - error: Error message (if failed)
        """
        old_contract = self.registry.get(contract_id)
        if not old_contract:
            return {
                'success': False,
                'error': "Contract not found",
            }

        # 1. Apply updates via version manager
        new_contract = self.version_manager.update(
            contract_id,
            changes,
            bump_type,
            changelog
        )

        if not new_contract:
            return {
                'success': False,
                'error': "Failed to update contract",
            }

        # 2. Generate change notifications
        notifications = self.watcher.notify_change(
            contract_id,
            old_contract,
            new_contract
        )

        # 3. Send notifications
        for notif in notifications:
            self.notifications.send(notif)

        return {
            'success': True,
            'contract': new_contract,
            'notifications_sent': len(notifications),
        }

    def deprecate_contract(
        self,
        contract_id: str,
        reason: str,
        sunset_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Mark a contract for deprecation.

        Updates status and notifies all consumers.

        Args:
            contract_id: Contract ID to deprecate
            reason: Reason for deprecation
            sunset_date: Optional date when contract will be retired

        Returns:
            Dictionary with:
            - success: Whether deprecation succeeded
            - error: Error message (if failed)
        """
        contract = self.registry.get(contract_id)
        if not contract:
            return {
                'success': False,
                'error': "Contract not found",
            }

        # 1. Update status
        if not self.registry.deprecate(contract_id, reason):
            return {
                'success': False,
                'error': "Failed to deprecate contract",
            }

        # 2. Generate deprecation notification
        notif = self.watcher.notify_deprecation(contract, reason, sunset_date)

        # 3. Send notification
        self.notifications.send(notif)

        return {
            'success': True,
        }

    def retire_contract(self, contract_id: str) -> Dict[str, Any]:
        """
        Retire a contract (mark as no longer available).

        Args:
            contract_id: Contract ID to retire

        Returns:
            Dictionary with:
            - success: Whether retirement succeeded
            - error: Error message (if failed)
        """
        contract = self.registry.get(contract_id)
        if not contract:
            return {
                'success': False,
                'error': "Contract not found",
            }

        # 1. Update status
        if not self.registry.retire(contract_id):
            return {
                'success': False,
                'error': "Failed to retire contract",
            }

        # 2. Notify all consumers
        self.notifications.broadcast_to_consumers(
            contract,
            NotificationType.CONTRACT_RETIRED,
            f"Contract '{contract.name}' has been retired and is no longer available.",
            NotificationPriority.CRITICAL
        )

        return {
            'success': True,
        }

    # =========================================================================
    # Consumer Management
    # =========================================================================

    def add_consumer(
        self,
        contract_id: str,
        team_id: str,
        team_name: str
    ) -> Dict[str, Any]:
        """
        Add a consumer to a contract.

        Registers the consumer and notifies the owner.

        Args:
            contract_id: Contract ID
            team_id: Consumer team ID
            team_name: Consumer team name

        Returns:
            Dictionary with:
            - success: Whether consumer was added
            - consumer: Created consumer (if successful)
            - error: Error message (if failed)
        """
        contract = self.registry.get(contract_id)
        if not contract:
            return {
                'success': False,
                'error': "Contract not found",
            }

        # Create consumer
        consumer = ContractConsumer(
            team_id=team_id,
            team_name=team_name,
            version_used=contract.version,
        )

        # Register consumer
        if not self.registry.add_consumer(contract_id, consumer):
            return {
                'success': False,
                'error': "Failed to add consumer (may already exist)",
            }

        # Notify owner
        notif = self.watcher.notify_new_consumer(contract, consumer)
        self.notifications.send(notif)

        return {
            'success': True,
            'consumer': consumer,
        }

    def remove_consumer(
        self,
        contract_id: str,
        team_id: str
    ) -> Dict[str, Any]:
        """
        Remove a consumer from a contract.

        Args:
            contract_id: Contract ID
            team_id: Consumer team ID to remove

        Returns:
            Dictionary with:
            - success: Whether consumer was removed
            - error: Error message (if failed)
        """
        contract = self.registry.get(contract_id)
        if not contract:
            return {
                'success': False,
                'error': "Contract not found",
            }

        # Find team name before removal
        team_name = team_id
        for consumer in contract.consumers:
            if consumer.team_id == team_id:
                team_name = consumer.team_name
                break

        # Remove consumer
        if not self.registry.remove_consumer(contract_id, team_id):
            return {
                'success': False,
                'error': "Consumer not found",
            }

        # Notify owner
        notif = self.watcher.notify_consumer_removed(contract, team_id, team_name)
        self.notifications.send(notif)

        return {
            'success': True,
        }

    def update_consumer_version(
        self,
        contract_id: str,
        team_id: str,
        new_version: ContractVersion
    ) -> Dict[str, Any]:
        """
        Update a consumer's used version.

        Args:
            contract_id: Contract ID
            team_id: Consumer team ID
            new_version: New version being used

        Returns:
            Dictionary with:
            - success: Whether update succeeded
            - error: Error message (if failed)
        """
        contract = self.registry.get(contract_id)
        if not contract:
            return {
                'success': False,
                'error': "Contract not found",
            }

        # Find and update consumer
        for consumer in contract.consumers:
            if consumer.team_id == team_id:
                consumer.version_used = new_version
                self.registry._save_contract(contract)
                return {
                    'success': True,
                }

        return {
            'success': False,
            'error': "Consumer not found",
        }

    # =========================================================================
    # Dashboard and Health
    # =========================================================================

    def get_team_dashboard(self, team_id: str) -> Dict[str, Any]:
        """
        Get dashboard information for a team.

        Includes owned contracts, consumed contracts, and notifications.

        Args:
            team_id: Team ID

        Returns:
            Dictionary with:
            - owned_contracts: Contracts owned by team
            - consumed_contracts: Contracts consumed by team
            - unread_notifications: Count of unread notifications
            - pending_actions: Count of pending action items
            - notification_stats: Notification statistics
        """
        owned = self.registry.get_contracts_by_owner(team_id)
        consumed = self.registry.get_contracts_by_consumer(team_id)
        unread = self.notifications.get_unread(team_id)
        pending = self.notifications.get_pending_actions(team_id)

        return {
            'owned_contracts': [
                {
                    'id': c.id,
                    'name': c.name,
                    'version': str(c.version),
                    'status': c.status.value,
                    'consumer_count': len(c.consumers),
                }
                for c in owned
            ],
            'consumed_contracts': [
                {
                    'id': c.id,
                    'name': c.name,
                    'version': str(c.version),
                    'status': c.status.value,
                    'owner': c.owner.team_name,
                }
                for c in consumed
            ],
            'unread_notifications': len(unread),
            'pending_actions': len(pending),
            'notification_stats': self.notifications.get_stats(team_id),
        }

    def get_contract_health(self, contract_id: str) -> Dict[str, Any]:
        """
        Get health information for a contract.

        Includes consumers, version history, dependencies, and validation.

        Args:
            contract_id: Contract ID

        Returns:
            Dictionary with:
            - contract: Contract details
            - consumers: List of consumers
            - version_history: Version history
            - dependencies: Dependency status
            - validation: Validation results
            - health_score: Overall health score
            - error: Error message (if not found)
        """
        contract = self.registry.get(contract_id)
        if not contract:
            return {
                'error': "Contract not found",
            }

        # Check dependencies
        deps = self.validator.check_dependencies(contract)

        # Validate contract
        validation_errors = self.validator.validate(contract)

        # Get version info
        versions = self.version_manager.list_versions(contract_id)
        changelog = self.version_manager.get_changelog(contract_id)

        # Calculate health score
        health_score = self._calculate_health_score(
            contract, validation_errors, deps
        )

        return {
            'contract': {
                'id': contract.id,
                'name': contract.name,
                'version': str(contract.version),
                'status': contract.status.value,
                'owner': {
                    'team_id': contract.owner.team_id,
                    'team_name': contract.owner.team_name,
                },
                'description': contract.description,
                'created_at': contract.created_at.isoformat(),
                'updated_at': contract.updated_at.isoformat(),
            },
            'consumers': [
                {
                    'team_id': c.team_id,
                    'team_name': c.team_name,
                    'version_used': str(c.version_used),
                    'registered_at': c.registered_at.isoformat(),
                }
                for c in contract.consumers
            ],
            'version_history': [str(v) for v in versions],
            'changelog': changelog,
            'dependencies': deps,
            'validation': {
                'valid': len(validation_errors) == 0,
                'errors': validation_errors,
            },
            'health_score': health_score,
        }

    def _calculate_health_score(
        self,
        contract: AnyContract,
        validation_errors: List[str],
        dependencies: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate a health score for a contract.

        Considers validation, dependencies, status, and consumer usage.

        Returns:
            Dictionary with:
            - score: Numeric score (0-100)
            - status: Health status (healthy, warning, critical)
            - issues: List of health issues
        """
        score = 100
        issues = []

        # Validation errors (-20 per error)
        for error in validation_errors:
            score -= 20
            issues.append(f"Validation: {error}")

        # Dependency issues (-15 per missing, -5 per deprecated)
        for missing in dependencies.get('missing', []):
            score -= 15
            issues.append(f"Missing dependency: {missing}")
        for mismatch in dependencies.get('version_mismatch', []):
            score -= 5
            issues.append(f"Dependency warning: {mismatch}")

        # Status penalties
        if contract.status == ContractStatus.DEPRECATED:
            score -= 20
            issues.append("Contract is deprecated")
        elif contract.status == ContractStatus.RETIRED:
            score = 0
            issues.append("Contract is retired")
        elif contract.status == ContractStatus.DRAFT:
            score -= 10
            issues.append("Contract is still in draft")

        # No consumers warning
        if contract.status == ContractStatus.APPROVED and len(contract.consumers) == 0:
            score -= 5
            issues.append("No consumers registered")

        # Clamp score
        score = max(0, min(100, score))

        # Determine status
        if score >= 80:
            status = "healthy"
        elif score >= 50:
            status = "warning"
        else:
            status = "critical"

        return {
            'score': score,
            'status': status,
            'issues': issues,
        }

    # =========================================================================
    # Search and Discovery
    # =========================================================================

    def search_contracts(
        self,
        query: str,
        contract_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for contracts.

        Args:
            query: Search query (searches name, description, tags)
            contract_type: Optional filter by type
            status: Optional filter by status

        Returns:
            List of matching contract summaries
        """
        # Get all matching contracts
        contracts = self.registry.search(query)

        # Apply additional filters
        if contract_type:
            contracts = [
                c for c in contracts
                if c.contract_type.value == contract_type
            ]

        if status:
            contracts = [
                c for c in contracts
                if c.status.value == status
            ]

        # Return summaries
        return [
            {
                'id': c.id,
                'name': c.name,
                'type': c.contract_type.value,
                'version': str(c.version),
                'status': c.status.value,
                'owner': c.owner.team_name,
                'description': c.description[:100] + '...' if len(c.description) > 100 else c.description,
            }
            for c in contracts
        ]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get overall system summary.

        Returns:
            Dictionary with:
            - total_contracts: Total number of contracts
            - by_type: Counts by contract type
            - by_status: Counts by status
            - total_consumers: Total consumer registrations
            - notification_stats: Notification statistics
        """
        storage_info = self.registry.get_storage_info()
        notification_info = self.notifications.get_storage_info()

        # Count total consumers across all contracts
        total_consumers = 0
        all_contracts = self.registry.list_contracts()
        for contract in all_contracts:
            total_consumers += len(contract.consumers)

        return {
            'total_contracts': storage_info['total_contracts'],
            'by_type': storage_info['type_counts'],
            'by_status': storage_info['status_counts'],
            'total_consumers': total_consumers,
            'notification_stats': self.notifications.get_stats(),
            'storage_info': {
                'contracts_size_bytes': storage_info['total_size_bytes'],
                'notifications_size_bytes': notification_info['total_size_bytes'],
            },
        }

    # =========================================================================
    # Bulk Operations
    # =========================================================================

    def validate_all_contracts(self) -> Dict[str, Any]:
        """
        Validate all contracts in the registry.

        Returns:
            Dictionary with:
            - total: Total contracts
            - valid: Number of valid contracts
            - invalid: Number of invalid contracts
            - errors: Dictionary of contract_id -> errors
        """
        errors = self.validator.validate_all()

        total = self.registry.count()
        invalid = len(errors)

        return {
            'total': total,
            'valid': total - invalid,
            'invalid': invalid,
            'errors': errors,
        }

    def check_all_dependencies(self) -> Dict[str, Any]:
        """
        Check dependencies for all contracts.

        Returns:
            Dictionary with:
            - total: Total contracts
            - satisfied: Contracts with satisfied dependencies
            - unsatisfied: Contracts with missing dependencies
            - issues: Dictionary of contract_id -> dependency issues
        """
        issues = self.validator.check_all_dependencies()

        total = self.registry.count()
        unsatisfied = len(issues)

        return {
            'total': total,
            'satisfied': total - unsatisfied,
            'unsatisfied': unsatisfied,
            'issues': issues,
        }
