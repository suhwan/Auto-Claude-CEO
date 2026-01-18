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

Storage location: `.planning/contracts/`
File format: JSON Schema based

Example usage:
    from extensions.ceo.team_contracts import (
        ContractType, ContractStatus, ContractVersion,
        ContractOwner, APIContract, APIEndpoint,
        ContractSerializer
    )

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

    # Serialize to JSON
    json_str = ContractSerializer.to_json(api)
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
]
