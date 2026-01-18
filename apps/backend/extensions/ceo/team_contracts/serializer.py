"""
Contract Serializer
===================

Provides JSON serialization and deserialization for Contract
and its specialized subclasses (APIContract, UIContract, DataContract).
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Union

from .models import (
    Contract,
    ContractConsumer,
    ContractOwner,
    ContractStatus,
    ContractType,
    ContractVersion,
)
from .api_schema import APIContract, APIEndpoint
from .ui_data_schema import (
    DataContract,
    EventDefinition,
    FieldDefinition,
    PropDefinition,
    SlotDefinition,
    UIContract,
)


class ContractSerializer:
    """
    Serializer for Contract and related models.

    Provides static methods to convert Contract objects to/from
    dictionaries and JSON strings. Handles datetime conversion
    using ISO 8601 format and properly serializes all contract types.
    """

    # ==========================================================================
    # DateTime Helpers
    # ==========================================================================

    @staticmethod
    def _datetime_to_str(dt: datetime) -> str:
        """Convert datetime to ISO format string."""
        return dt.isoformat()

    @staticmethod
    def _str_to_datetime(dt_str: str) -> datetime:
        """Convert ISO format string to datetime."""
        return datetime.fromisoformat(dt_str)

    # ==========================================================================
    # Version Serialization
    # ==========================================================================

    @staticmethod
    def version_to_dict(version: ContractVersion) -> Dict[str, int]:
        """
        Convert ContractVersion to dictionary.

        Args:
            version: ContractVersion instance

        Returns:
            Dictionary with major, minor, patch keys
        """
        return {
            'major': version.major,
            'minor': version.minor,
            'patch': version.patch,
        }

    @staticmethod
    def version_from_dict(data: Dict[str, int]) -> ContractVersion:
        """
        Create ContractVersion from dictionary.

        Args:
            data: Dictionary with major, minor, patch keys

        Returns:
            ContractVersion instance
        """
        return ContractVersion(
            major=data.get('major', 1),
            minor=data.get('minor', 0),
            patch=data.get('patch', 0),
        )

    # ==========================================================================
    # Owner/Consumer Serialization
    # ==========================================================================

    @staticmethod
    def _owner_to_dict(owner: ContractOwner) -> Dict[str, Any]:
        """Convert ContractOwner to dictionary."""
        return {
            'team_id': owner.team_id,
            'team_name': owner.team_name,
            'contact': owner.contact,
        }

    @staticmethod
    def _owner_from_dict(data: Dict[str, Any]) -> ContractOwner:
        """Create ContractOwner from dictionary."""
        return ContractOwner(
            team_id=data['team_id'],
            team_name=data['team_name'],
            contact=data.get('contact'),
        )

    @staticmethod
    def _consumer_to_dict(consumer: ContractConsumer) -> Dict[str, Any]:
        """Convert ContractConsumer to dictionary."""
        return {
            'team_id': consumer.team_id,
            'team_name': consumer.team_name,
            'version_used': ContractSerializer.version_to_dict(consumer.version_used),
            'registered_at': ContractSerializer._datetime_to_str(consumer.registered_at),
        }

    @staticmethod
    def _consumer_from_dict(data: Dict[str, Any]) -> ContractConsumer:
        """Create ContractConsumer from dictionary."""
        return ContractConsumer(
            team_id=data['team_id'],
            team_name=data['team_name'],
            version_used=ContractSerializer.version_from_dict(data.get('version_used', {})),
            registered_at=ContractSerializer._str_to_datetime(data['registered_at']),
        )

    # ==========================================================================
    # API Schema Serialization
    # ==========================================================================

    @staticmethod
    def _endpoint_to_dict(endpoint: APIEndpoint) -> Dict[str, Any]:
        """Convert APIEndpoint to dictionary."""
        return {
            'path': endpoint.path,
            'method': endpoint.method,
            'description': endpoint.description,
            'path_params': endpoint.path_params,
            'query_params': endpoint.query_params,
            'headers': endpoint.headers,
            'request_body': endpoint.request_body,
            'response': endpoint.response,
            'auth_required': endpoint.auth_required,
            'permissions': endpoint.permissions,
        }

    @staticmethod
    def _endpoint_from_dict(data: Dict[str, Any]) -> APIEndpoint:
        """Create APIEndpoint from dictionary."""
        return APIEndpoint(
            path=data['path'],
            method=data['method'],
            description=data.get('description', ''),
            path_params=data.get('path_params', {}),
            query_params=data.get('query_params', {}),
            headers=data.get('headers', {}),
            request_body=data.get('request_body'),
            response=data.get('response', {}),
            auth_required=data.get('auth_required', True),
            permissions=data.get('permissions', []),
        )

    # ==========================================================================
    # UI Schema Serialization
    # ==========================================================================

    @staticmethod
    def _prop_to_dict(prop: PropDefinition) -> Dict[str, Any]:
        """Convert PropDefinition to dictionary."""
        return {
            'name': prop.name,
            'prop_type': prop.prop_type,
            'required': prop.required,
            'default': prop.default,
            'description': prop.description,
            'validation': prop.validation,
        }

    @staticmethod
    def _prop_from_dict(data: Dict[str, Any]) -> PropDefinition:
        """Create PropDefinition from dictionary."""
        return PropDefinition(
            name=data['name'],
            prop_type=data['prop_type'],
            required=data.get('required', False),
            default=data.get('default'),
            description=data.get('description', ''),
            validation=data.get('validation'),
        )

    @staticmethod
    def _event_to_dict(event: EventDefinition) -> Dict[str, Any]:
        """Convert EventDefinition to dictionary."""
        return {
            'name': event.name,
            'payload': event.payload,
            'description': event.description,
        }

    @staticmethod
    def _event_from_dict(data: Dict[str, Any]) -> EventDefinition:
        """Create EventDefinition from dictionary."""
        return EventDefinition(
            name=data['name'],
            payload=data.get('payload', {}),
            description=data.get('description', ''),
        )

    @staticmethod
    def _slot_to_dict(slot: SlotDefinition) -> Dict[str, Any]:
        """Convert SlotDefinition to dictionary."""
        return {
            'name': slot.name,
            'description': slot.description,
            'scope_props': slot.scope_props,
        }

    @staticmethod
    def _slot_from_dict(data: Dict[str, Any]) -> SlotDefinition:
        """Create SlotDefinition from dictionary."""
        return SlotDefinition(
            name=data['name'],
            description=data.get('description', ''),
            scope_props=data.get('scope_props', {}),
        )

    # ==========================================================================
    # Data Schema Serialization
    # ==========================================================================

    @staticmethod
    def _field_to_dict(field_def: FieldDefinition) -> Dict[str, Any]:
        """Convert FieldDefinition to dictionary."""
        return {
            'name': field_def.name,
            'field_type': field_def.field_type,
            'required': field_def.required,
            'nullable': field_def.nullable,
            'description': field_def.description,
            'constraints': field_def.constraints,
        }

    @staticmethod
    def _field_from_dict(data: Dict[str, Any]) -> FieldDefinition:
        """Create FieldDefinition from dictionary."""
        return FieldDefinition(
            name=data['name'],
            field_type=data['field_type'],
            required=data.get('required', False),
            nullable=data.get('nullable', True),
            description=data.get('description', ''),
            constraints=data.get('constraints', {}),
        )

    # ==========================================================================
    # Contract Serialization
    # ==========================================================================

    @staticmethod
    def contract_to_dict(
        contract: Union[Contract, APIContract, UIContract, DataContract]
    ) -> Dict[str, Any]:
        """
        Convert Contract to dictionary.

        Handles all contract types (base, API, UI, Data) and includes
        all type-specific fields.

        Args:
            contract: Contract instance to serialize

        Returns:
            Dictionary representation
        """
        # Base contract fields
        data: Dict[str, Any] = {
            'id': contract.id,
            'name': contract.name,
            'contract_type': contract.contract_type.value,
            'version': ContractSerializer.version_to_dict(contract.version),
            'status': contract.status.value,
            'owner': ContractSerializer._owner_to_dict(contract.owner),
            'consumers': [
                ContractSerializer._consumer_to_dict(c) for c in contract.consumers
            ],
            'schema': contract.schema,
            'description': contract.description,
            'tags': contract.tags,
            'created_at': ContractSerializer._datetime_to_str(contract.created_at),
            'updated_at': ContractSerializer._datetime_to_str(contract.updated_at),
            'changelog': contract.changelog,
            'depends_on': contract.depends_on,
        }

        # API-specific fields
        if isinstance(contract, APIContract):
            data['base_url'] = contract.base_url
            data['endpoints'] = [
                ContractSerializer._endpoint_to_dict(e) for e in contract.endpoints
            ]
            data['shared_schemas'] = contract.shared_schemas
            data['error_codes'] = contract.error_codes

        # UI-specific fields
        elif isinstance(contract, UIContract):
            data['component_name'] = contract.component_name
            data['props'] = [
                ContractSerializer._prop_to_dict(p) for p in contract.props
            ]
            data['events'] = [
                ContractSerializer._event_to_dict(e) for e in contract.events
            ]
            data['slots'] = [
                ContractSerializer._slot_to_dict(s) for s in contract.slots
            ]
            data['css_classes'] = contract.css_classes
            data['theme_variables'] = contract.theme_variables

        # Data-specific fields
        elif isinstance(contract, DataContract):
            data['model_name'] = contract.model_name
            data['fields'] = [
                ContractSerializer._field_to_dict(f) for f in contract.fields
            ]
            data['relations'] = contract.relations
            data['indexes'] = contract.indexes
            data['validation_rules'] = contract.validation_rules

        return data

    @staticmethod
    def contract_from_dict(
        data: Dict[str, Any]
    ) -> Union[Contract, APIContract, UIContract, DataContract]:
        """
        Create Contract from dictionary.

        Automatically determines the contract type from the data
        and creates the appropriate subclass.

        Args:
            data: Dictionary containing contract data

        Returns:
            Contract instance (or appropriate subclass)
        """
        contract_type = ContractType(data['contract_type'])

        # Common fields
        base_kwargs = {
            'id': data['id'],
            'name': data['name'],
            'contract_type': contract_type,
            'version': ContractSerializer.version_from_dict(data['version']),
            'status': ContractStatus(data['status']),
            'owner': ContractSerializer._owner_from_dict(data['owner']),
            'consumers': [
                ContractSerializer._consumer_from_dict(c)
                for c in data.get('consumers', [])
            ],
            'schema': data.get('schema', {}),
            'description': data.get('description', ''),
            'tags': data.get('tags', []),
            'created_at': ContractSerializer._str_to_datetime(data['created_at']),
            'updated_at': ContractSerializer._str_to_datetime(data['updated_at']),
            'changelog': data.get('changelog', []),
            'depends_on': data.get('depends_on', []),
        }

        # Create appropriate contract type
        if contract_type == ContractType.API:
            return APIContract(
                **base_kwargs,
                base_url=data.get('base_url', ''),
                endpoints=[
                    ContractSerializer._endpoint_from_dict(e)
                    for e in data.get('endpoints', [])
                ],
                shared_schemas=data.get('shared_schemas', {}),
                error_codes=data.get('error_codes', {}),
            )

        elif contract_type == ContractType.UI:
            return UIContract(
                **base_kwargs,
                component_name=data.get('component_name', ''),
                props=[
                    ContractSerializer._prop_from_dict(p)
                    for p in data.get('props', [])
                ],
                events=[
                    ContractSerializer._event_from_dict(e)
                    for e in data.get('events', [])
                ],
                slots=[
                    ContractSerializer._slot_from_dict(s)
                    for s in data.get('slots', [])
                ],
                css_classes=data.get('css_classes', []),
                theme_variables=data.get('theme_variables', {}),
            )

        elif contract_type == ContractType.DATA:
            return DataContract(
                **base_kwargs,
                model_name=data.get('model_name', ''),
                fields=[
                    ContractSerializer._field_from_dict(f)
                    for f in data.get('fields', [])
                ],
                relations=data.get('relations', {}),
                indexes=data.get('indexes', []),
                validation_rules=data.get('validation_rules', []),
            )

        # Default: base Contract
        return Contract(**base_kwargs)

    # ==========================================================================
    # JSON Serialization
    # ==========================================================================

    @staticmethod
    def to_json(
        contract: Union[Contract, APIContract, UIContract, DataContract],
        indent: int = 2
    ) -> str:
        """
        Serialize Contract to JSON string.

        Args:
            contract: Contract instance to serialize
            indent: JSON indentation level (default: 2)

        Returns:
            JSON string representation
        """
        return json.dumps(
            ContractSerializer.contract_to_dict(contract),
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(
        json_str: str
    ) -> Union[Contract, APIContract, UIContract, DataContract]:
        """
        Deserialize Contract from JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            Contract instance (or appropriate subclass)
        """
        data = json.loads(json_str)
        return ContractSerializer.contract_from_dict(data)

    # ==========================================================================
    # Batch Serialization
    # ==========================================================================

    @staticmethod
    def contracts_to_dict(
        contracts: List[Union[Contract, APIContract, UIContract, DataContract]]
    ) -> List[Dict[str, Any]]:
        """
        Convert list of Contracts to list of dictionaries.

        Args:
            contracts: List of Contract instances

        Returns:
            List of dictionary representations
        """
        return [ContractSerializer.contract_to_dict(c) for c in contracts]

    @staticmethod
    def contracts_from_dict(
        data_list: List[Dict[str, Any]]
    ) -> List[Union[Contract, APIContract, UIContract, DataContract]]:
        """
        Create list of Contracts from list of dictionaries.

        Args:
            data_list: List of dictionaries

        Returns:
            List of Contract instances
        """
        return [ContractSerializer.contract_from_dict(d) for d in data_list]

    @staticmethod
    def contracts_to_json(
        contracts: List[Union[Contract, APIContract, UIContract, DataContract]],
        indent: int = 2
    ) -> str:
        """
        Serialize list of Contracts to JSON string.

        Args:
            contracts: List of Contract instances
            indent: JSON indentation level (default: 2)

        Returns:
            JSON string representation
        """
        return json.dumps(
            ContractSerializer.contracts_to_dict(contracts),
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def contracts_from_json(
        json_str: str
    ) -> List[Union[Contract, APIContract, UIContract, DataContract]]:
        """
        Deserialize list of Contracts from JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            List of Contract instances
        """
        data_list = json.loads(json_str)
        return ContractSerializer.contracts_from_dict(data_list)
