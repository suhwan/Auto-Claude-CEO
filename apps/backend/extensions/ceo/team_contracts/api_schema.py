"""
API Contract Schema
===================

Specialized contract types for REST/GraphQL API interfaces.
Defines API endpoints, request/response schemas, authentication,
and error codes.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models import Contract, ContractType, ContractStatus, ContractVersion, ContractOwner


@dataclass
class APIEndpoint:
    """
    API endpoint definition.

    Describes a single API endpoint with its path, method,
    parameters, and request/response schemas.

    Attributes:
        path: URL path pattern (e.g., "/api/v1/users/{id}")
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        description: Human-readable description
        path_params: Path parameter definitions (JSON Schema)
        query_params: Query parameter definitions (JSON Schema)
        headers: Required/optional header definitions
        request_body: Request body schema (JSON Schema, optional)
        response: Response schemas by status code
        auth_required: Whether authentication is required
        permissions: Required permissions/scopes
    """
    path: str
    method: str  # GET, POST, PUT, DELETE, PATCH
    description: str = ""

    # Parameters
    path_params: Dict[str, Any] = field(default_factory=dict)
    # { "id": { "type": "string", "format": "uuid" } }

    query_params: Dict[str, Any] = field(default_factory=dict)
    # { "page": { "type": "integer", "default": 1 } }

    headers: Dict[str, Any] = field(default_factory=dict)
    # { "X-Request-ID": { "type": "string", "required": false } }

    # Request/Response
    request_body: Optional[Dict[str, Any]] = None
    # { "type": "object", "properties": { "name": {...} }, "required": [...] }

    response: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # {
    #   "200": { "description": "Success", "schema": {...} },
    #   "400": { "description": "Bad Request", "schema": {...} },
    #   "404": { "description": "Not Found", "schema": {...} }
    # }

    # Authentication and Authorization
    auth_required: bool = True
    permissions: List[str] = field(default_factory=list)
    # ["users:read", "users:write"]

    def is_read_only(self) -> bool:
        """Check if endpoint is read-only (GET or HEAD)."""
        return self.method.upper() in ('GET', 'HEAD', 'OPTIONS')

    def has_body(self) -> bool:
        """Check if endpoint accepts a request body."""
        return self.method.upper() in ('POST', 'PUT', 'PATCH')


@dataclass
class APIContract(Contract):
    """
    API-specific contract.

    Extends the base Contract with API-specific fields for
    base URL, endpoints, shared schemas, and error codes.

    Attributes:
        base_url: Base URL path for all endpoints (e.g., "/api/v1")
        endpoints: List of API endpoint definitions
        shared_schemas: Reusable schema definitions referenced by endpoints
        error_codes: Application-specific error codes and descriptions
    """
    base_url: str = ""
    endpoints: List[APIEndpoint] = field(default_factory=list)

    # Shared schemas for reuse across endpoints
    shared_schemas: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # {
    #   "User": { "type": "object", "properties": {...} },
    #   "PaginatedResponse": { "type": "object", "properties": {...} }
    # }

    # Error code definitions
    error_codes: Dict[str, str] = field(default_factory=dict)
    # {
    #   "USER_NOT_FOUND": "User with given ID not found",
    #   "INVALID_EMAIL": "Email format is invalid"
    # }

    def __post_init__(self):
        """Ensure contract_type is set to API."""
        # Override contract_type to ensure it's always API
        if self.contract_type != ContractType.API:
            object.__setattr__(self, 'contract_type', ContractType.API)

    def add_endpoint(self, endpoint: APIEndpoint) -> None:
        """
        Add an endpoint to the contract.

        Args:
            endpoint: APIEndpoint to add
        """
        self.endpoints.append(endpoint)

    def remove_endpoint(self, path: str, method: str) -> bool:
        """
        Remove an endpoint by path and method.

        Args:
            path: Endpoint path
            method: HTTP method

        Returns:
            True if endpoint was removed, False if not found
        """
        original_count = len(self.endpoints)
        self.endpoints = [
            e for e in self.endpoints
            if not (e.path == path and e.method.upper() == method.upper())
        ]
        return len(self.endpoints) < original_count

    def get_endpoint(self, path: str, method: str) -> Optional[APIEndpoint]:
        """
        Get an endpoint by path and method.

        Args:
            path: Endpoint path
            method: HTTP method

        Returns:
            APIEndpoint if found, None otherwise
        """
        for endpoint in self.endpoints:
            if endpoint.path == path and endpoint.method.upper() == method.upper():
                return endpoint
        return None

    def list_paths(self) -> List[str]:
        """Get list of unique paths."""
        return list(set(e.path for e in self.endpoints))

    def add_shared_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """
        Add a shared schema definition.

        Args:
            name: Schema name (e.g., "User", "PaginatedResponse")
            schema: JSON Schema definition
        """
        self.shared_schemas[name] = schema

    def add_error_code(self, code: str, description: str) -> None:
        """
        Add an error code definition.

        Args:
            code: Error code (e.g., "USER_NOT_FOUND")
            description: Human-readable description
        """
        self.error_codes[code] = description


def create_api_contract(
    contract_id: str,
    name: str,
    owner: ContractOwner,
    base_url: str = "",
    version: Optional[ContractVersion] = None,
    status: ContractStatus = ContractStatus.DRAFT,
    description: str = "",
) -> APIContract:
    """
    Factory function to create an API contract.

    Args:
        contract_id: Unique contract ID
        name: Contract name
        owner: Contract owner
        base_url: Base URL for endpoints
        version: Contract version (defaults to 1.0.0)
        status: Initial status (defaults to DRAFT)
        description: Contract description

    Returns:
        New APIContract instance
    """
    return APIContract(
        id=contract_id,
        name=name,
        contract_type=ContractType.API,
        version=version or ContractVersion(1, 0, 0),
        status=status,
        owner=owner,
        base_url=base_url,
        description=description,
    )
