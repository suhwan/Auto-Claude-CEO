"""
Contract Registry
=================

Provides file system-based storage and management for Contract instances.
Supports CRUD operations, consumer management, status transitions, and search.

Storage structure:
    .planning/contracts/
    ├── index.json              # Contract index (id -> metadata)
    ├── api/
    │   ├── user-api/
    │   │   ├── contract.json   # Current version
    │   │   └── history/        # Version history
    │   │       ├── 1.0.0.json
    │   │       └── 1.1.0.json
    │   └── auth-api/
    │       └── contract.json
    ├── ui/
    └── data/
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .models import (
    Contract,
    ContractConsumer,
    ContractStatus,
    ContractType,
    ContractVersion,
)
from .api_schema import APIContract
from .ui_data_schema import DataContract, UIContract
from .serializer import ContractSerializer


class ContractRegistry:
    """
    Contract registry with file-based storage.

    Provides contract registration, retrieval, search, consumer management,
    and status lifecycle operations.

    Attributes:
        project_path: Path to the project root directory
        contracts_dir: Path to the contracts storage directory
    """

    # Default storage directory relative to project path
    DEFAULT_STORAGE_DIR = ".planning/contracts"

    # Index file name
    INDEX_FILE = "index.json"

    # Contract file name within type/name directory
    CONTRACT_FILE = "contract.json"

    # History subdirectory name
    HISTORY_SUBDIR = "history"

    def __init__(self, project_path: str):
        """
        Initialize ContractRegistry.

        Args:
            project_path: Path to the project root directory
        """
        self.project_path = Path(project_path)
        self.contracts_dir = self.project_path / self.DEFAULT_STORAGE_DIR
        self.contracts_dir.mkdir(parents=True, exist_ok=True)
        self._index: Dict[str, Dict[str, Any]] = {}
        self._load_index()

    # =========================================================================
    # Index Management
    # =========================================================================

    def _load_index(self) -> None:
        """Load the contract index from file."""
        index_path = self.contracts_dir / self.INDEX_FILE
        if index_path.exists():
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    self._index = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._index = {}
        else:
            self._index = {}

    def _save_index(self) -> None:
        """Save the contract index to file."""
        index_path = self.contracts_dir / self.INDEX_FILE
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(self._index, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving index: {e}")

    def _update_index_entry(
        self,
        contract: Union[Contract, APIContract, UIContract, DataContract]
    ) -> None:
        """Update the index entry for a contract."""
        self._index[contract.id] = {
            'id': contract.id,
            'name': contract.name,
            'contract_type': contract.contract_type.value,
            'version': str(contract.version),
            'status': contract.status.value,
            'owner_team_id': contract.owner.team_id,
            'owner_team_name': contract.owner.team_name,
            'description': contract.description,
            'tags': contract.tags,
            'consumer_count': len(contract.consumers),
            'updated_at': contract.updated_at.isoformat(),
        }

    def _remove_index_entry(self, contract_id: str) -> None:
        """Remove a contract from the index."""
        if contract_id in self._index:
            del self._index[contract_id]

    # =========================================================================
    # Path Helpers
    # =========================================================================

    def _get_contract_dir(
        self,
        contract: Union[Contract, APIContract, UIContract, DataContract]
    ) -> Path:
        """Get the directory path for a contract."""
        type_dir = contract.contract_type.value
        name_slug = self._slugify(contract.name)
        return self.contracts_dir / type_dir / name_slug

    def _get_contract_path(
        self,
        contract: Union[Contract, APIContract, UIContract, DataContract]
    ) -> Path:
        """Get the file path for a contract."""
        return self._get_contract_dir(contract) / self.CONTRACT_FILE

    def _get_history_dir(
        self,
        contract: Union[Contract, APIContract, UIContract, DataContract]
    ) -> Path:
        """Get the history directory path for a contract."""
        return self._get_contract_dir(contract) / self.HISTORY_SUBDIR

    def _slugify(self, name: str) -> str:
        """Convert a name to a URL-friendly slug."""
        return name.lower().replace(' ', '-').replace('_', '-')

    def _find_contract_path_by_id(self, contract_id: str) -> Optional[Path]:
        """Find the contract file path by ID from the index."""
        if contract_id not in self._index:
            return None

        entry = self._index[contract_id]
        contract_type = entry.get('contract_type', '')
        name = entry.get('name', '')

        if not contract_type or not name:
            return None

        name_slug = self._slugify(name)
        contract_path = self.contracts_dir / contract_type / name_slug / self.CONTRACT_FILE

        return contract_path if contract_path.exists() else None

    # =========================================================================
    # Registration and Retrieval
    # =========================================================================

    def register(
        self,
        contract: Union[Contract, APIContract, UIContract, DataContract]
    ) -> bool:
        """
        Register a new contract.

        Args:
            contract: Contract instance to register

        Returns:
            True if registration was successful, False otherwise
        """
        # Check for duplicate ID
        if contract.id in self._index:
            print(f"Contract with ID '{contract.id}' already exists")
            return False

        # Check for duplicate name within same type
        for entry in self._index.values():
            if (entry['name'] == contract.name and
                entry['contract_type'] == contract.contract_type.value):
                print(f"Contract with name '{contract.name}' already exists "
                      f"for type '{contract.contract_type.value}'")
                return False

        return self._save_contract(contract, is_new=True)

    def _save_contract(
        self,
        contract: Union[Contract, APIContract, UIContract, DataContract],
        is_new: bool = False
    ) -> bool:
        """
        Save a contract to file.

        Args:
            contract: Contract instance to save
            is_new: Whether this is a new contract (affects index behavior)

        Returns:
            True if save was successful, False otherwise
        """
        try:
            contract_dir = self._get_contract_dir(contract)
            contract_dir.mkdir(parents=True, exist_ok=True)

            contract_path = self._get_contract_path(contract)

            # Update timestamps
            if is_new:
                contract.created_at = datetime.now()
            contract.updated_at = datetime.now()

            # Serialize and write
            json_content = ContractSerializer.to_json(contract)
            with open(contract_path, 'w', encoding='utf-8') as f:
                f.write(json_content)

            # Update index
            self._update_index_entry(contract)
            self._save_index()

            return True

        except IOError as e:
            print(f"Error saving contract: {e}")
            return False

    def get(
        self,
        contract_id: str
    ) -> Optional[Union[Contract, APIContract, UIContract, DataContract]]:
        """
        Get a contract by ID.

        Args:
            contract_id: Unique contract identifier

        Returns:
            Contract instance if found, None otherwise
        """
        contract_path = self._find_contract_path_by_id(contract_id)
        if not contract_path:
            return None

        try:
            with open(contract_path, 'r', encoding='utf-8') as f:
                json_content = f.read()
            return ContractSerializer.from_json(json_content)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading contract: {e}")
            return None

    def get_by_name(
        self,
        name: str,
        contract_type: Optional[ContractType] = None
    ) -> Optional[Union[Contract, APIContract, UIContract, DataContract]]:
        """
        Get a contract by name.

        Args:
            name: Contract name
            contract_type: Optional filter by contract type

        Returns:
            Contract instance if found, None otherwise
        """
        for entry in self._index.values():
            if entry['name'] == name:
                if contract_type is None or entry['contract_type'] == contract_type.value:
                    return self.get(entry['id'])
        return None

    def list_contracts(
        self,
        contract_type: Optional[ContractType] = None,
        status: Optional[ContractStatus] = None,
        owner_team: Optional[str] = None
    ) -> List[Union[Contract, APIContract, UIContract, DataContract]]:
        """
        List contracts with optional filtering.

        Args:
            contract_type: Filter by contract type
            status: Filter by status
            owner_team: Filter by owner team ID

        Returns:
            List of matching contracts
        """
        contracts = []

        for entry in self._index.values():
            # Apply filters
            if contract_type and entry['contract_type'] != contract_type.value:
                continue
            if status and entry['status'] != status.value:
                continue
            if owner_team and entry['owner_team_id'] != owner_team:
                continue

            contract = self.get(entry['id'])
            if contract:
                contracts.append(contract)

        return contracts

    def search(
        self,
        query: str
    ) -> List[Union[Contract, APIContract, UIContract, DataContract]]:
        """
        Search contracts by name, description, or tags.

        Args:
            query: Search query string (case-insensitive)

        Returns:
            List of matching contracts
        """
        query_lower = query.lower()
        matches = []

        for entry in self._index.values():
            # Check name
            if query_lower in entry.get('name', '').lower():
                matches.append(entry['id'])
                continue

            # Check description
            if query_lower in entry.get('description', '').lower():
                matches.append(entry['id'])
                continue

            # Check tags
            tags = entry.get('tags', [])
            if any(query_lower in tag.lower() for tag in tags):
                matches.append(entry['id'])
                continue

        return [self.get(cid) for cid in matches if self.get(cid)]

    def delete(self, contract_id: str) -> bool:
        """
        Delete a contract.

        Args:
            contract_id: Contract ID to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        contract = self.get(contract_id)
        if not contract:
            return False

        try:
            import shutil
            contract_dir = self._get_contract_dir(contract)
            if contract_dir.exists():
                shutil.rmtree(contract_dir)

            # Remove from index
            self._remove_index_entry(contract_id)
            self._save_index()

            return True
        except IOError as e:
            print(f"Error deleting contract: {e}")
            return False

    # =========================================================================
    # Consumer Management
    # =========================================================================

    def add_consumer(
        self,
        contract_id: str,
        consumer: ContractConsumer
    ) -> bool:
        """
        Add a consumer to a contract.

        Args:
            contract_id: Contract ID
            consumer: ContractConsumer instance to add

        Returns:
            True if consumer was added, False otherwise
        """
        contract = self.get(contract_id)
        if not contract:
            return False

        # Check if consumer already exists
        for existing in contract.consumers:
            if existing.team_id == consumer.team_id:
                print(f"Consumer '{consumer.team_id}' already exists")
                return False

        contract.add_consumer(consumer)
        return self._save_contract(contract)

    def remove_consumer(self, contract_id: str, team_id: str) -> bool:
        """
        Remove a consumer from a contract.

        Args:
            contract_id: Contract ID
            team_id: Team ID of the consumer to remove

        Returns:
            True if consumer was removed, False otherwise
        """
        contract = self.get(contract_id)
        if not contract:
            return False

        if contract.remove_consumer(team_id):
            return self._save_contract(contract)
        return False

    def get_consumers(self, contract_id: str) -> List[ContractConsumer]:
        """
        Get all consumers of a contract.

        Args:
            contract_id: Contract ID

        Returns:
            List of ContractConsumer instances
        """
        contract = self.get(contract_id)
        if not contract:
            return []
        return contract.consumers

    def get_contracts_by_consumer(
        self,
        team_id: str
    ) -> List[Union[Contract, APIContract, UIContract, DataContract]]:
        """
        Get all contracts consumed by a team.

        Args:
            team_id: Team ID of the consumer

        Returns:
            List of contracts the team consumes
        """
        result = []
        for entry in self._index.values():
            contract = self.get(entry['id'])
            if contract:
                for consumer in contract.consumers:
                    if consumer.team_id == team_id:
                        result.append(contract)
                        break
        return result

    def get_contracts_by_owner(
        self,
        team_id: str
    ) -> List[Union[Contract, APIContract, UIContract, DataContract]]:
        """
        Get all contracts owned by a team.

        Args:
            team_id: Team ID of the owner

        Returns:
            List of contracts the team owns
        """
        return self.list_contracts(owner_team=team_id)

    # =========================================================================
    # Status Management
    # =========================================================================

    def update_status(
        self,
        contract_id: str,
        status: ContractStatus
    ) -> bool:
        """
        Update the status of a contract.

        Args:
            contract_id: Contract ID
            status: New status

        Returns:
            True if status was updated, False otherwise
        """
        contract = self.get(contract_id)
        if not contract:
            return False

        contract.status = status
        return self._save_contract(contract)

    def deprecate(
        self,
        contract_id: str,
        reason: str
    ) -> bool:
        """
        Mark a contract as deprecated.

        Adds a changelog entry with the deprecation reason.

        Args:
            contract_id: Contract ID
            reason: Reason for deprecation

        Returns:
            True if deprecation was successful, False otherwise
        """
        contract = self.get(contract_id)
        if not contract:
            return False

        contract.status = ContractStatus.DEPRECATED
        contract.changelog.append({
            'version': str(contract.version),
            'changes': f"DEPRECATED: {reason}",
            'date': datetime.now().isoformat(),
            'breaking': False,
        })

        return self._save_contract(contract)

    def retire(self, contract_id: str) -> bool:
        """
        Mark a contract as retired.

        Adds a changelog entry recording the retirement.

        Args:
            contract_id: Contract ID

        Returns:
            True if retirement was successful, False otherwise
        """
        contract = self.get(contract_id)
        if not contract:
            return False

        contract.status = ContractStatus.RETIRED
        contract.changelog.append({
            'version': str(contract.version),
            'changes': "Contract retired",
            'date': datetime.now().isoformat(),
            'breaking': True,
        })

        return self._save_contract(contract)

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def exists(self, contract_id: str) -> bool:
        """
        Check if a contract exists.

        Args:
            contract_id: Contract ID to check

        Returns:
            True if contract exists, False otherwise
        """
        return contract_id in self._index

    def count(
        self,
        contract_type: Optional[ContractType] = None,
        status: Optional[ContractStatus] = None
    ) -> int:
        """
        Count contracts with optional filtering.

        Args:
            contract_type: Filter by contract type
            status: Filter by status

        Returns:
            Number of matching contracts
        """
        count = 0
        for entry in self._index.values():
            if contract_type and entry['contract_type'] != contract_type.value:
                continue
            if status and entry['status'] != status.value:
                continue
            count += 1
        return count

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about the registry storage.

        Returns:
            Dictionary with storage statistics
        """
        total_size = 0
        if self.contracts_dir.exists():
            for file in self.contracts_dir.rglob('*.json'):
                total_size += file.stat().st_size

        type_counts = {}
        status_counts = {}
        for entry in self._index.values():
            ctype = entry.get('contract_type', 'unknown')
            cstatus = entry.get('status', 'unknown')
            type_counts[ctype] = type_counts.get(ctype, 0) + 1
            status_counts[cstatus] = status_counts.get(cstatus, 0) + 1

        return {
            'storage_path': str(self.contracts_dir),
            'total_contracts': len(self._index),
            'type_counts': type_counts,
            'status_counts': status_counts,
            'total_size_bytes': total_size,
        }
