"""
Team Contracts Module
=====================

Provides data models and utilities for team contracts (shared contracts).
Team contracts define standardized interfaces for cross-team collaboration:

- **API Contracts**: REST/GraphQL endpoint specifications
- **UI Contracts**: Component props, events, and slots
- **Data Contracts**: Data model schemas and relations

This module provides:
- Base contract models (Contract, ContractVersion, ContractOwner, ContractConsumer)
- API-specific models (APIEndpoint, APIContract)
- UI-specific models (PropDefinition, EventDefinition, SlotDefinition, UIContract)
- Data-specific models (FieldDefinition, DataContract)
- JSON serialization utilities (ContractSerializer)
- Registry for contract storage and retrieval
- Version management for semantic versioning
- Validation and compatibility checking
- Change notification system
- Unified service facade

Storage location: `.planning/contracts/`
File format: JSON Schema based

Example usage:
    from extensions.ceo.team_contracts import (
        TeamContractService, ContractType, ContractStatus,
        ContractVersion, ContractOwner, APIContract, APIEndpoint
    )

    # Create service instance
    service = TeamContractService('/path/to/project')

    # Create an API contract
    owner = ContractOwner("dev-team", "Development Team")
    api = APIContract(
        id="api-001",
        name="User API",
        contract_type=ContractType.API,
        version=ContractVersion(1, 0, 0),
        status=ContractStatus.DRAFT,
        owner=owner,
        base_url="/api/v1",
        endpoints=[
            APIEndpoint("/users/{id}", "GET", "Get user by ID")
        ]
    )

    # Create contract (validates and registers)
    result = service.create_contract(api)

    # Add a consumer
    service.add_consumer("api-001", "frontend-team", "Frontend Team")

    # Update contract with notifications
    service.update_contract("api-001", {"description": "Updated"}, "patch")

    # Get team dashboard
    dashboard = service.get_team_dashboard("dev-team")
"""

from .models import (
    Contract,
    ContractConsumer,
    ContractOwner,
    ContractStatus,
    ContractType,
    ContractVersion,
)
from .api_schema import APIContract, APIEndpoint, create_api_contract
from .ui_data_schema import (
    DataContract,
    EventDefinition,
    FieldDefinition,
    PropDefinition,
    SlotDefinition,
    UIContract,
    create_data_contract,
    create_ui_contract,
)
from .serializer import ContractSerializer
from .registry import ContractRegistry
from .version_manager import ContractVersionManager
from .validator import ContractValidator
from .notification_models import (
    Notification,
    NotificationPriority,
    NotificationRecipient,
    NotificationStatus,
    NotificationSubscription,
    NotificationType,
)
from .watcher import ContractWatcher
from .notification_service import NotificationService
from .service import TeamContractService

__all__ = [
    # Enums
    "ContractType",
    "ContractStatus",
    # Base Models
    "ContractVersion",
    "ContractOwner",
    "ContractConsumer",
    "Contract",
    # API Contract
    "APIEndpoint",
    "APIContract",
    "create_api_contract",
    # UI Contract
    "PropDefinition",
    "EventDefinition",
    "SlotDefinition",
    "UIContract",
    "create_ui_contract",
    # Data Contract
    "FieldDefinition",
    "DataContract",
    "create_data_contract",
    # Serializer
    "ContractSerializer",
    # Registry
    "ContractRegistry",
    # Version Manager
    "ContractVersionManager",
    # Validator
    "ContractValidator",
    # Notification Models
    "NotificationType",
    "NotificationPriority",
    "NotificationStatus",
    "NotificationRecipient",
    "Notification",
    "NotificationSubscription",
    # Watcher
    "ContractWatcher",
    # Notification Service
    "NotificationService",
    # Unified Service
    "TeamContractService",
]
