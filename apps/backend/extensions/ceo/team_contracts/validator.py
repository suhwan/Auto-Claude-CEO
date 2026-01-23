"""
Contract Validator
==================

Provides validation and compatibility checking for contracts.
Includes field validation, contract type-specific validation,
compatibility checking between versions, and dependency validation.
"""

from typing import Any, Dict, List, Optional, Set, Union

from .models import (
    Contract,
    ContractConsumer,
    ContractStatus,
    ContractVersion,
)
from .api_schema import APIContract, APIEndpoint
from .ui_data_schema import DataContract, FieldDefinition, PropDefinition, UIContract


# Type alias for any contract type
AnyContract = Union[Contract, APIContract, UIContract, DataContract]


class ContractValidator:
    """
    Contract validation and compatibility checking.

    Provides validation for contract structure and content,
    compatibility checking between versions, and dependency
    resolution verification.

    Attributes:
        registry: ContractRegistry instance for dependency checks
    """

    # Valid HTTP methods for API contracts
    VALID_HTTP_METHODS = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'}

    # Valid field types for data contracts
    VALID_FIELD_TYPES = {'string', 'number', 'boolean', 'date', 'object', 'array'}

    # Valid prop types for UI contracts
    VALID_PROP_TYPES = {'string', 'number', 'boolean', 'object', 'array', 'function'}

    def __init__(self, registry: 'ContractRegistry'):  # noqa: F821
        """
        Initialize ContractValidator.

        Args:
            registry: ContractRegistry instance for dependency checks
        """
        self.registry = registry

    # =========================================================================
    # Basic Validation
    # =========================================================================

    def validate(self, contract: AnyContract) -> List[str]:
        """
        Validate a contract and return list of errors.

        Performs both common validation and type-specific validation.

        Args:
            contract: Contract to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Common field validation
        if not contract.id:
            errors.append("Contract ID is required")
        if not contract.name:
            errors.append("Contract name is required")
        if not contract.owner:
            errors.append("Contract owner is required")
        elif not contract.owner.team_id:
            errors.append("Contract owner team_id is required")

        # Version validation
        if contract.version.major < 0 or contract.version.minor < 0 or contract.version.patch < 0:
            errors.append("Version numbers must be non-negative")

        # Type-specific validation
        if isinstance(contract, APIContract):
            errors.extend(self._validate_api_contract(contract))
        elif isinstance(contract, UIContract):
            errors.extend(self._validate_ui_contract(contract))
        elif isinstance(contract, DataContract):
            errors.extend(self._validate_data_contract(contract))

        return errors

    def is_valid(self, contract: AnyContract) -> bool:
        """
        Check if a contract is valid.

        Args:
            contract: Contract to validate

        Returns:
            True if valid (no errors), False otherwise
        """
        return len(self.validate(contract)) == 0

    # =========================================================================
    # Type-Specific Validation
    # =========================================================================

    def _validate_api_contract(self, contract: APIContract) -> List[str]:
        """
        Validate API contract specific fields.

        Args:
            contract: API contract to validate

        Returns:
            List of error messages
        """
        errors = []

        # Validate each endpoint
        for i, endpoint in enumerate(contract.endpoints):
            endpoint_errors = self._validate_endpoint(endpoint, i)
            errors.extend(endpoint_errors)

        # Check for duplicate endpoints (same path + method)
        seen_endpoints: Set[tuple] = set()
        for endpoint in contract.endpoints:
            key = (endpoint.path, endpoint.method.upper())
            if key in seen_endpoints:
                errors.append(f"Duplicate endpoint: {endpoint.method.upper()} {endpoint.path}")
            seen_endpoints.add(key)

        return errors

    def _validate_endpoint(self, endpoint: APIEndpoint, index: int) -> List[str]:
        """
        Validate a single API endpoint.

        Args:
            endpoint: Endpoint to validate
            index: Index in the endpoints list (for error messages)

        Returns:
            List of error messages
        """
        errors = []
        prefix = f"Endpoint [{index}]"

        if not endpoint.path:
            errors.append(f"{prefix}: Path is required")
        elif not endpoint.path.startswith('/'):
            errors.append(f"{prefix}: Path must start with '/'")

        if not endpoint.method:
            errors.append(f"{prefix}: Method is required")
        elif endpoint.method.upper() not in self.VALID_HTTP_METHODS:
            errors.append(f"{prefix}: Invalid method '{endpoint.method}'. "
                         f"Must be one of {self.VALID_HTTP_METHODS}")

        # Validate path parameters match path
        if endpoint.path_params:
            path_vars = self._extract_path_variables(endpoint.path)
            for param in endpoint.path_params.keys():
                if param not in path_vars:
                    errors.append(f"{prefix}: Path parameter '{param}' "
                                 f"not found in path '{endpoint.path}'")

        return errors

    def _extract_path_variables(self, path: str) -> Set[str]:
        """Extract variable names from a path like /users/{id}/posts/{post_id}."""
        import re
        return set(re.findall(r'\{([^}]+)\}', path))

    def _validate_ui_contract(self, contract: UIContract) -> List[str]:
        """
        Validate UI contract specific fields.

        Args:
            contract: UI contract to validate

        Returns:
            List of error messages
        """
        errors = []

        if not contract.component_name:
            errors.append("Component name is required for UI contracts")

        # Validate props
        seen_props: Set[str] = set()
        for i, prop in enumerate(contract.props):
            if not prop.name:
                errors.append(f"Prop [{i}]: Name is required")
            elif prop.name in seen_props:
                errors.append(f"Prop [{i}]: Duplicate prop name '{prop.name}'")
            else:
                seen_props.add(prop.name)

            if prop.prop_type and prop.prop_type not in self.VALID_PROP_TYPES:
                errors.append(f"Prop '{prop.name}': Invalid type '{prop.prop_type}'. "
                             f"Must be one of {self.VALID_PROP_TYPES}")

        # Validate events
        seen_events: Set[str] = set()
        for i, event in enumerate(contract.events):
            if not event.name:
                errors.append(f"Event [{i}]: Name is required")
            elif event.name in seen_events:
                errors.append(f"Event [{i}]: Duplicate event name '{event.name}'")
            else:
                seen_events.add(event.name)

        # Validate slots
        seen_slots: Set[str] = set()
        for i, slot in enumerate(contract.slots):
            if not slot.name:
                errors.append(f"Slot [{i}]: Name is required")
            elif slot.name in seen_slots:
                errors.append(f"Slot [{i}]: Duplicate slot name '{slot.name}'")
            else:
                seen_slots.add(slot.name)

        return errors

    def _validate_data_contract(self, contract: DataContract) -> List[str]:
        """
        Validate Data contract specific fields.

        Args:
            contract: Data contract to validate

        Returns:
            List of error messages
        """
        errors = []

        if not contract.model_name:
            errors.append("Model name is required for Data contracts")

        # Validate fields
        seen_fields: Set[str] = set()
        for i, field in enumerate(contract.fields):
            if not field.name:
                errors.append(f"Field [{i}]: Name is required")
            elif field.name in seen_fields:
                errors.append(f"Field [{i}]: Duplicate field name '{field.name}'")
            else:
                seen_fields.add(field.name)

            if field.field_type and field.field_type not in self.VALID_FIELD_TYPES:
                errors.append(f"Field '{field.name}': Invalid type '{field.field_type}'. "
                             f"Must be one of {self.VALID_FIELD_TYPES}")

        # Validate indexes reference existing fields
        for i, index_fields in enumerate(contract.indexes):
            for field_name in index_fields:
                if field_name not in seen_fields:
                    errors.append(f"Index [{i}]: References non-existent field '{field_name}'")

        return errors

    # =========================================================================
    # Compatibility Checking
    # =========================================================================

    def check_compatibility(
        self,
        old_contract: AnyContract,
        new_contract: AnyContract
    ) -> Dict[str, Any]:
        """
        Check compatibility between two versions of a contract.

        Identifies breaking changes, additions, and modifications.

        Args:
            old_contract: Previous version of the contract
            new_contract: New version of the contract

        Returns:
            Dictionary with compatibility analysis:
            - compatible: True if backward compatible
            - breaking_changes: List of breaking changes
            - additions: List of non-breaking additions
            - modifications: List of modifications
        """
        result = {
            'compatible': True,
            'breaking_changes': [],
            'additions': [],
            'modifications': [],
        }

        # Check version compatibility
        if not new_contract.version.is_compatible_with(old_contract.version):
            result['compatible'] = False
            result['breaking_changes'].append(
                f"Major version changed: {old_contract.version} -> {new_contract.version}"
            )

        # Type-specific compatibility checks
        if isinstance(old_contract, APIContract) and isinstance(new_contract, APIContract):
            self._check_api_compatibility(old_contract, new_contract, result)
        elif isinstance(old_contract, UIContract) and isinstance(new_contract, UIContract):
            self._check_ui_compatibility(old_contract, new_contract, result)
        elif isinstance(old_contract, DataContract) and isinstance(new_contract, DataContract):
            self._check_data_compatibility(old_contract, new_contract, result)

        return result

    def _check_api_compatibility(
        self,
        old: APIContract,
        new: APIContract,
        result: Dict[str, Any]
    ) -> None:
        """
        Check API contract compatibility.

        Breaking changes:
        - Removed endpoints
        - Added required parameters
        - Changed response schema (removing fields)

        Args:
            old: Old API contract
            new: New API contract
            result: Result dictionary to update
        """
        old_endpoints = {(e.path, e.method.upper()): e for e in old.endpoints}
        new_endpoints = {(e.path, e.method.upper()): e for e in new.endpoints}

        # Check for removed endpoints (breaking)
        for key, endpoint in old_endpoints.items():
            if key not in new_endpoints:
                result['compatible'] = False
                result['breaking_changes'].append(
                    f"Removed endpoint: {endpoint.method.upper()} {endpoint.path}"
                )

        # Check for added endpoints (non-breaking)
        for key, endpoint in new_endpoints.items():
            if key not in old_endpoints:
                result['additions'].append(
                    f"Added endpoint: {endpoint.method.upper()} {endpoint.path}"
                )

        # Check for modified endpoints
        for key in old_endpoints.keys() & new_endpoints.keys():
            old_ep = old_endpoints[key]
            new_ep = new_endpoints[key]

            # Check for added required query parameters (breaking)
            old_required = set(
                k for k, v in old_ep.query_params.items()
                if isinstance(v, dict) and v.get('required', False)
            )
            new_required = set(
                k for k, v in new_ep.query_params.items()
                if isinstance(v, dict) and v.get('required', False)
            )

            added_required = new_required - old_required
            if added_required:
                result['compatible'] = False
                result['breaking_changes'].append(
                    f"Endpoint {old_ep.method} {old_ep.path}: "
                    f"Added required parameters: {added_required}"
                )

            # Check for removed response fields (potentially breaking)
            # This is a simplified check - full schema comparison would be more complex
            if old_ep.response and new_ep.response:
                old_status_codes = set(old_ep.response.keys())
                new_status_codes = set(new_ep.response.keys())
                removed_codes = old_status_codes - new_status_codes
                if removed_codes:
                    result['modifications'].append(
                        f"Endpoint {old_ep.method} {old_ep.path}: "
                        f"Removed response status codes: {removed_codes}"
                    )

    def _check_ui_compatibility(
        self,
        old: UIContract,
        new: UIContract,
        result: Dict[str, Any]
    ) -> None:
        """
        Check UI contract compatibility.

        Breaking changes:
        - Removed required props
        - Added required props
        - Removed events

        Args:
            old: Old UI contract
            new: New UI contract
            result: Result dictionary to update
        """
        old_props = {p.name: p for p in old.props}
        new_props = {p.name: p for p in new.props}

        # Check for removed props
        for name, prop in old_props.items():
            if name not in new_props:
                if prop.required:
                    result['compatible'] = False
                    result['breaking_changes'].append(f"Removed required prop: {name}")
                else:
                    result['modifications'].append(f"Removed optional prop: {name}")

        # Check for added required props (breaking for existing consumers)
        for name, prop in new_props.items():
            if name not in old_props:
                if prop.required:
                    result['compatible'] = False
                    result['breaking_changes'].append(f"Added required prop: {name}")
                else:
                    result['additions'].append(f"Added optional prop: {name}")

        # Check for modified props
        for name in old_props.keys() & new_props.keys():
            old_prop = old_props[name]
            new_prop = new_props[name]

            # Required changed from false to true (breaking)
            if not old_prop.required and new_prop.required:
                result['compatible'] = False
                result['breaking_changes'].append(f"Prop '{name}' changed to required")

            # Type changed (potentially breaking)
            if old_prop.prop_type != new_prop.prop_type:
                result['modifications'].append(
                    f"Prop '{name}' type changed: {old_prop.prop_type} -> {new_prop.prop_type}"
                )

        # Check events
        old_events = {e.name for e in old.events}
        new_events = {e.name for e in new.events}

        removed_events = old_events - new_events
        if removed_events:
            result['modifications'].append(f"Removed events: {removed_events}")

        added_events = new_events - old_events
        if added_events:
            result['additions'].append(f"Added events: {added_events}")

    def _check_data_compatibility(
        self,
        old: DataContract,
        new: DataContract,
        result: Dict[str, Any]
    ) -> None:
        """
        Check Data contract compatibility.

        Breaking changes:
        - Removed required fields
        - Added required fields (for existing data)
        - Field type changes

        Args:
            old: Old Data contract
            new: New Data contract
            result: Result dictionary to update
        """
        old_fields = {f.name: f for f in old.fields}
        new_fields = {f.name: f for f in new.fields}

        # Check for removed fields
        for name, field in old_fields.items():
            if name not in new_fields:
                if field.required:
                    result['compatible'] = False
                    result['breaking_changes'].append(f"Removed required field: {name}")
                else:
                    result['modifications'].append(f"Removed optional field: {name}")

        # Check for added required fields (breaking for existing data)
        for name, field in new_fields.items():
            if name not in old_fields:
                if field.required and not field.nullable:
                    result['compatible'] = False
                    result['breaking_changes'].append(
                        f"Added required non-nullable field: {name}"
                    )
                else:
                    result['additions'].append(f"Added field: {name}")

        # Check for modified fields
        for name in old_fields.keys() & new_fields.keys():
            old_field = old_fields[name]
            new_field = new_fields[name]

            # Type changed (breaking)
            if old_field.field_type != new_field.field_type:
                result['compatible'] = False
                result['breaking_changes'].append(
                    f"Field '{name}' type changed: "
                    f"{old_field.field_type} -> {new_field.field_type}"
                )

            # Required changed from false to true (potentially breaking)
            if not old_field.required and new_field.required:
                result['compatible'] = False
                result['breaking_changes'].append(
                    f"Field '{name}' changed to required"
                )

            # Nullable changed from true to false (breaking)
            if old_field.nullable and not new_field.nullable:
                result['compatible'] = False
                result['breaking_changes'].append(
                    f"Field '{name}' changed to non-nullable"
                )

    # =========================================================================
    # Dependency Checking
    # =========================================================================

    def check_dependencies(self, contract: AnyContract) -> Dict[str, Any]:
        """
        Check if contract dependencies are satisfied.

        Verifies that all contracts listed in depends_on exist
        and are not retired.

        Args:
            contract: Contract to check dependencies for

        Returns:
            Dictionary with dependency analysis:
            - satisfied: True if all dependencies met
            - missing: List of missing dependency IDs
            - version_mismatch: List of version/status issues
        """
        result = {
            'satisfied': True,
            'missing': [],
            'version_mismatch': [],
        }

        for dep_id in contract.depends_on:
            dep_contract = self.registry.get(dep_id)

            if not dep_contract:
                result['satisfied'] = False
                result['missing'].append(dep_id)
            elif dep_contract.status == ContractStatus.RETIRED:
                result['satisfied'] = False
                result['version_mismatch'].append(
                    f"{dep_id}: Contract is retired"
                )
            elif dep_contract.status == ContractStatus.DEPRECATED:
                # Deprecated is a warning, not a failure
                result['version_mismatch'].append(
                    f"{dep_id}: Contract is deprecated"
                )

        return result

    def find_breaking_consumers(
        self,
        contract_id: str
    ) -> List[ContractConsumer]:
        """
        Find consumers that would be affected by breaking changes.

        Identifies consumers using versions that are not compatible
        with the current contract version.

        Args:
            contract_id: Contract ID to check

        Returns:
            List of affected ContractConsumer instances
        """
        contract = self.registry.get(contract_id)
        if not contract:
            return []

        affected = []
        for consumer in contract.consumers:
            if not contract.version.is_compatible_with(consumer.version_used):
                affected.append(consumer)

        return affected

    def get_dependents(self, contract_id: str) -> List[AnyContract]:
        """
        Get all contracts that depend on a given contract.

        Args:
            contract_id: Contract ID to find dependents for

        Returns:
            List of contracts that depend on the given contract
        """
        dependents = []

        for entry in self.registry._index.values():
            contract = self.registry.get(entry['id'])
            if contract and contract_id in contract.depends_on:
                dependents.append(contract)

        return dependents

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def validate_all(self) -> Dict[str, List[str]]:
        """
        Validate all contracts in the registry.

        Returns:
            Dictionary mapping contract IDs to their validation errors
            (only includes contracts with errors)
        """
        results = {}

        for entry in self.registry._index.values():
            contract = self.registry.get(entry['id'])
            if contract:
                errors = self.validate(contract)
                if errors:
                    results[contract.id] = errors

        return results

    def check_all_dependencies(self) -> Dict[str, Dict[str, Any]]:
        """
        Check dependencies for all contracts in the registry.

        Returns:
            Dictionary mapping contract IDs to their dependency check results
            (only includes contracts with unsatisfied dependencies)
        """
        results = {}

        for entry in self.registry._index.values():
            contract = self.registry.get(entry['id'])
            if contract:
                dep_result = self.check_dependencies(contract)
                if not dep_result['satisfied']:
                    results[contract.id] = dep_result

        return results
