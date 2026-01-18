"""
UI and Data Contract Schemas
============================

Specialized contract types for UI components and data models.
Defines component props, events, slots for UI contracts and
field definitions, relations, indexes for data contracts.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models import Contract, ContractType, ContractStatus, ContractVersion, ContractOwner


# =============================================================================
# UI Contract Types
# =============================================================================

@dataclass
class PropDefinition:
    """
    UI component prop definition.

    Describes a single prop for a UI component including type,
    validation rules, and documentation.

    Attributes:
        name: Prop name
        prop_type: Type of the prop (string, number, boolean, object, array)
        required: Whether the prop is required
        default: Default value if not provided
        description: Human-readable description
        validation: Optional validation rules (JSON Schema format)
    """
    name: str
    prop_type: str  # string, number, boolean, object, array, function
    required: bool = False
    default: Any = None
    description: str = ""
    validation: Optional[Dict[str, Any]] = None
    # { "minLength": 1, "maxLength": 100, "pattern": "^[a-z]+$" }


@dataclass
class EventDefinition:
    """
    UI component event definition.

    Describes an event emitted by a UI component.

    Attributes:
        name: Event name (e.g., "onChange", "onSubmit")
        payload: Schema for event payload (JSON Schema format)
        description: Human-readable description
    """
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)
    # { "type": "object", "properties": { "value": { "type": "string" } } }
    description: str = ""


@dataclass
class SlotDefinition:
    """
    UI component slot definition.

    Describes a slot for content projection in UI components.

    Attributes:
        name: Slot name (e.g., "default", "header", "footer")
        description: Human-readable description
        scope_props: Props exposed to slot content
    """
    name: str
    description: str = ""
    scope_props: Dict[str, str] = field(default_factory=dict)
    # { "item": "object", "index": "number" }


@dataclass
class UIContract(Contract):
    """
    UI component contract.

    Extends the base Contract with UI-specific fields for
    component props, events, slots, and styling.

    Attributes:
        component_name: Name of the UI component
        props: List of prop definitions
        events: List of event definitions
        slots: List of slot definitions
        css_classes: Available CSS classes
        theme_variables: Theme/CSS variable names and descriptions
    """
    component_name: str = ""
    props: List[PropDefinition] = field(default_factory=list)
    events: List[EventDefinition] = field(default_factory=list)
    slots: List[SlotDefinition] = field(default_factory=list)

    # Styling
    css_classes: List[str] = field(default_factory=list)
    # ["btn", "btn-primary", "btn-secondary"]

    theme_variables: Dict[str, str] = field(default_factory=dict)
    # { "--btn-bg-color": "Button background color" }

    def __post_init__(self):
        """Ensure contract_type is set to UI."""
        if self.contract_type != ContractType.UI:
            object.__setattr__(self, 'contract_type', ContractType.UI)

    def add_prop(self, prop: PropDefinition) -> None:
        """Add a prop definition."""
        self.props.append(prop)

    def add_event(self, event: EventDefinition) -> None:
        """Add an event definition."""
        self.events.append(event)

    def add_slot(self, slot: SlotDefinition) -> None:
        """Add a slot definition."""
        self.slots.append(slot)

    def get_prop(self, name: str) -> Optional[PropDefinition]:
        """Get a prop by name."""
        for prop in self.props:
            if prop.name == name:
                return prop
        return None

    def get_required_props(self) -> List[PropDefinition]:
        """Get list of required props."""
        return [p for p in self.props if p.required]

    def list_prop_names(self) -> List[str]:
        """Get list of prop names."""
        return [p.name for p in self.props]

    def list_event_names(self) -> List[str]:
        """Get list of event names."""
        return [e.name for e in self.events]


# =============================================================================
# Data Contract Types
# =============================================================================

@dataclass
class FieldDefinition:
    """
    Data model field definition.

    Describes a single field in a data model including type,
    constraints, and documentation.

    Attributes:
        name: Field name
        field_type: Data type (string, number, boolean, date, object, array)
        required: Whether the field is required
        nullable: Whether the field can be null
        description: Human-readable description
        constraints: Validation constraints (JSON Schema format)
    """
    name: str
    field_type: str  # string, number, boolean, date, object, array
    required: bool = False
    nullable: bool = True
    description: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)
    # { "minLength": 1, "maxLength": 100, "pattern": "^[a-z]+$" }


@dataclass
class DataContract(Contract):
    """
    Data model contract.

    Extends the base Contract with data model-specific fields for
    fields, relations, indexes, and validation rules.

    Attributes:
        model_name: Name of the data model
        fields: List of field definitions
        relations: Relationships to other models
        indexes: Database indexes
        validation_rules: Business validation rules
    """
    model_name: str = ""
    fields: List[FieldDefinition] = field(default_factory=list)

    # Relationships to other models
    relations: Dict[str, str] = field(default_factory=dict)
    # { "author": "User", "comments": "Comment[]" }

    # Database indexes
    indexes: List[List[str]] = field(default_factory=list)
    # [["email"], ["created_at", "status"]]

    # Business validation rules (expressed as strings)
    validation_rules: List[str] = field(default_factory=list)
    # ["end_date > start_date", "quantity >= 0"]

    def __post_init__(self):
        """Ensure contract_type is set to DATA."""
        if self.contract_type != ContractType.DATA:
            object.__setattr__(self, 'contract_type', ContractType.DATA)

    def add_field(self, field_def: FieldDefinition) -> None:
        """Add a field definition."""
        self.fields.append(field_def)

    def remove_field(self, name: str) -> bool:
        """Remove a field by name."""
        original_count = len(self.fields)
        self.fields = [f for f in self.fields if f.name != name]
        return len(self.fields) < original_count

    def get_field(self, name: str) -> Optional[FieldDefinition]:
        """Get a field by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def get_required_fields(self) -> List[FieldDefinition]:
        """Get list of required fields."""
        return [f for f in self.fields if f.required]

    def list_field_names(self) -> List[str]:
        """Get list of field names."""
        return [f.name for f in self.fields]

    def add_relation(self, field_name: str, target_model: str) -> None:
        """
        Add a relation to another model.

        Args:
            field_name: Name of the relation field
            target_model: Target model name (use [] suffix for arrays)
        """
        self.relations[field_name] = target_model

    def add_index(self, columns: List[str]) -> None:
        """
        Add a database index.

        Args:
            columns: List of column names for the index
        """
        self.indexes.append(columns)

    def add_validation_rule(self, rule: str) -> None:
        """
        Add a business validation rule.

        Args:
            rule: Validation rule expression
        """
        self.validation_rules.append(rule)


# =============================================================================
# Factory Functions
# =============================================================================

def create_ui_contract(
    contract_id: str,
    name: str,
    owner: ContractOwner,
    component_name: str,
    version: Optional[ContractVersion] = None,
    status: ContractStatus = ContractStatus.DRAFT,
    description: str = "",
) -> UIContract:
    """
    Factory function to create a UI contract.

    Args:
        contract_id: Unique contract ID
        name: Contract name
        owner: Contract owner
        component_name: UI component name
        version: Contract version (defaults to 1.0.0)
        status: Initial status (defaults to DRAFT)
        description: Contract description

    Returns:
        New UIContract instance
    """
    return UIContract(
        id=contract_id,
        name=name,
        contract_type=ContractType.UI,
        version=version or ContractVersion(1, 0, 0),
        status=status,
        owner=owner,
        component_name=component_name,
        description=description,
    )


def create_data_contract(
    contract_id: str,
    name: str,
    owner: ContractOwner,
    model_name: str,
    version: Optional[ContractVersion] = None,
    status: ContractStatus = ContractStatus.DRAFT,
    description: str = "",
) -> DataContract:
    """
    Factory function to create a Data contract.

    Args:
        contract_id: Unique contract ID
        name: Contract name
        owner: Contract owner
        model_name: Data model name
        version: Contract version (defaults to 1.0.0)
        status: Initial status (defaults to DRAFT)
        description: Contract description

    Returns:
        New DataContract instance
    """
    return DataContract(
        id=contract_id,
        name=name,
        contract_type=ContractType.DATA,
        version=version or ContractVersion(1, 0, 0),
        status=status,
        owner=owner,
        model_name=model_name,
        description=description,
    )
