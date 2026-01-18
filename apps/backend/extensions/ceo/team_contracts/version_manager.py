"""
Contract Version Manager
========================

Provides version management capabilities for contracts including
version bumping, changelog management, version history, rollback,
and version comparison.

Version history is stored in a history/ subdirectory within each
contract's directory, with each version saved as {version}.json.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .models import (
    Contract,
    ContractVersion,
)
from .api_schema import APIContract
from .ui_data_schema import DataContract, UIContract
from .serializer import ContractSerializer


# Type alias for any contract type
AnyContract = Union[Contract, APIContract, UIContract, DataContract]


class ContractVersionManager:
    """
    Contract version management.

    Provides version bumping, changelog tracking, version history
    archival, rollback, and version comparison functionality.

    Requires a ContractRegistry instance for contract access.

    Attributes:
        registry: ContractRegistry instance for contract operations
    """

    def __init__(self, registry: 'ContractRegistry'):  # noqa: F821
        """
        Initialize ContractVersionManager.

        Args:
            registry: ContractRegistry instance
        """
        self.registry = registry

    # =========================================================================
    # Version Updates
    # =========================================================================

    def update(
        self,
        contract_id: str,
        changes: Dict[str, Any],
        bump_type: str = "patch",
        changelog_entry: str = ""
    ) -> Optional[AnyContract]:
        """
        Update a contract with version bump.

        Archives the current version to history, applies changes,
        and bumps the version according to bump_type.

        Args:
            contract_id: Contract ID to update
            changes: Dictionary of field changes to apply
            bump_type: Version bump type: "major", "minor", or "patch"
            changelog_entry: Description of changes for changelog

        Returns:
            Updated contract if successful, None otherwise
        """
        contract = self.registry.get(contract_id)
        if not contract:
            return None

        # Archive current version to history
        self._archive_version(contract)

        # Store old version for changelog
        old_version = contract.version

        # Bump version based on type
        if bump_type == "major":
            contract.version = old_version.bump_major()
        elif bump_type == "minor":
            contract.version = old_version.bump_minor()
        else:
            contract.version = old_version.bump_patch()

        # Apply changes
        for key, value in changes.items():
            if hasattr(contract, key):
                setattr(contract, key, value)

        # Add changelog entry
        contract.changelog.append({
            'version': str(contract.version),
            'previous_version': str(old_version),
            'changes': changelog_entry,
            'date': datetime.now().isoformat(),
            'breaking': bump_type == "major",
        })

        # Update timestamp
        contract.updated_at = datetime.now()

        # Save updated contract
        if self.registry._save_contract(contract):
            return contract
        return None

    # =========================================================================
    # Version Retrieval
    # =========================================================================

    def get_version(
        self,
        contract_id: str,
        version: str
    ) -> Optional[AnyContract]:
        """
        Get a specific version of a contract from history.

        Args:
            contract_id: Contract ID
            version: Version string (e.g., "1.0.0")

        Returns:
            Contract at specified version if found, None otherwise
        """
        contract = self.registry.get(contract_id)
        if not contract:
            return None

        # Check if requesting current version
        if str(contract.version) == version:
            return contract

        # Look in history
        history_dir = self._get_history_dir(contract)
        version_file = history_dir / f"{version}.json"

        if not version_file.exists():
            return None

        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                json_content = f.read()
            return ContractSerializer.from_json(json_content)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading version {version}: {e}")
            return None

    def list_versions(self, contract_id: str) -> List[ContractVersion]:
        """
        List all available versions of a contract.

        Returns versions in ascending order (oldest first).

        Args:
            contract_id: Contract ID

        Returns:
            List of ContractVersion objects
        """
        contract = self.registry.get(contract_id)
        if not contract:
            return []

        versions = []

        # Get versions from history
        history_dir = self._get_history_dir(contract)
        if history_dir.exists():
            for file in history_dir.iterdir():
                if file.is_file() and file.suffix == '.json':
                    version_str = file.stem
                    try:
                        version = ContractVersion.from_string(version_str)
                        versions.append(version)
                    except (ValueError, IndexError):
                        continue

        # Add current version
        versions.append(contract.version)

        # Sort by version (major, minor, patch)
        versions.sort(key=lambda v: (v.major, v.minor, v.patch))

        return versions

    def get_changelog(self, contract_id: str) -> List[Dict[str, Any]]:
        """
        Get the changelog for a contract.

        Returns changelog entries in chronological order (oldest first).

        Args:
            contract_id: Contract ID

        Returns:
            List of changelog entry dictionaries
        """
        contract = self.registry.get(contract_id)
        if not contract:
            return []

        return contract.changelog

    # =========================================================================
    # Rollback
    # =========================================================================

    def rollback(
        self,
        contract_id: str,
        target_version: str
    ) -> Optional[AnyContract]:
        """
        Rollback a contract to a previous version.

        Archives the current version, restores the target version
        as a new version, and records the rollback in changelog.

        Args:
            contract_id: Contract ID
            target_version: Version string to rollback to

        Returns:
            Contract at rolled back version if successful, None otherwise
        """
        contract = self.registry.get(contract_id)
        if not contract:
            return None

        # Load target version
        target = self.get_version(contract_id, target_version)
        if not target:
            print(f"Target version {target_version} not found")
            return None

        # Archive current version
        self._archive_version(contract)

        # Store old version for changelog
        old_version = contract.version

        # Bump patch version (rollback is a patch operation)
        new_version = contract.version.bump_patch()

        # Copy fields from target to current contract
        # Preserve metadata fields
        preserved_id = contract.id
        preserved_created_at = contract.created_at
        preserved_changelog = contract.changelog.copy()

        # Update contract from target (using serialization to copy all fields)
        target_dict = ContractSerializer.contract_to_dict(target)
        restored = ContractSerializer.contract_from_dict(target_dict)

        # Restore preserved fields
        restored.id = preserved_id
        restored.created_at = preserved_created_at
        restored.changelog = preserved_changelog
        restored.version = new_version
        restored.updated_at = datetime.now()

        # Add rollback changelog entry
        restored.changelog.append({
            'version': str(new_version),
            'previous_version': str(old_version),
            'changes': f"Rollback to version {target_version}",
            'date': datetime.now().isoformat(),
            'breaking': False,
            'rollback': True,
            'target_version': target_version,
        })

        # Save restored contract
        if self.registry._save_contract(restored):
            return restored
        return None

    # =========================================================================
    # Version Comparison
    # =========================================================================

    def compare_versions(
        self,
        contract_id: str,
        version_a: str,
        version_b: str
    ) -> Dict[str, Any]:
        """
        Compare two versions of a contract.

        Returns a detailed comparison of differences between versions.

        Args:
            contract_id: Contract ID
            version_a: First version string
            version_b: Second version string

        Returns:
            Dictionary with comparison results including:
            - versions: The two versions being compared
            - additions: Fields/values added in version_b
            - removals: Fields/values removed in version_b
            - modifications: Fields changed between versions
        """
        result = {
            'versions': {'a': version_a, 'b': version_b},
            'additions': {},
            'removals': {},
            'modifications': {},
        }

        contract_a = self.get_version(contract_id, version_a)
        contract_b = self.get_version(contract_id, version_b)

        if not contract_a:
            result['error'] = f"Version {version_a} not found"
            return result
        if not contract_b:
            result['error'] = f"Version {version_b} not found"
            return result

        # Convert to dicts for comparison
        dict_a = ContractSerializer.contract_to_dict(contract_a)
        dict_b = ContractSerializer.contract_to_dict(contract_b)

        # Fields to skip in comparison (metadata that always changes)
        skip_fields = {'version', 'updated_at', 'changelog'}

        # Find additions, removals, and modifications
        all_keys = set(dict_a.keys()) | set(dict_b.keys())

        for key in all_keys:
            if key in skip_fields:
                continue

            in_a = key in dict_a
            in_b = key in dict_b

            if in_a and not in_b:
                result['removals'][key] = dict_a[key]
            elif not in_a and in_b:
                result['additions'][key] = dict_b[key]
            elif dict_a[key] != dict_b[key]:
                result['modifications'][key] = {
                    'old': dict_a[key],
                    'new': dict_b[key],
                }

        return result

    # =========================================================================
    # History Management
    # =========================================================================

    def _archive_version(self, contract: AnyContract) -> bool:
        """
        Archive the current version of a contract to history.

        Args:
            contract: Contract to archive

        Returns:
            True if archival was successful, False otherwise
        """
        try:
            history_dir = self._get_history_dir(contract)
            history_dir.mkdir(parents=True, exist_ok=True)

            version_file = history_dir / f"{contract.version}.json"

            # Don't overwrite if version already archived
            if version_file.exists():
                return True

            # Serialize and write
            json_content = ContractSerializer.to_json(contract)
            with open(version_file, 'w', encoding='utf-8') as f:
                f.write(json_content)

            return True

        except IOError as e:
            print(f"Error archiving version: {e}")
            return False

    def _get_history_dir(self, contract: AnyContract) -> Path:
        """
        Get the history directory path for a contract.

        Args:
            contract: Contract instance

        Returns:
            Path to history directory
        """
        return self.registry._get_contract_dir(contract) / self.registry.HISTORY_SUBDIR

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_latest_version(self, contract_id: str) -> Optional[ContractVersion]:
        """
        Get the latest version of a contract.

        Args:
            contract_id: Contract ID

        Returns:
            Latest ContractVersion if found, None otherwise
        """
        versions = self.list_versions(contract_id)
        return versions[-1] if versions else None

    def get_version_count(self, contract_id: str) -> int:
        """
        Get the number of versions for a contract.

        Args:
            contract_id: Contract ID

        Returns:
            Number of versions (including current)
        """
        return len(self.list_versions(contract_id))

    def has_breaking_changes(self, contract_id: str) -> bool:
        """
        Check if a contract has any breaking changes in its history.

        Args:
            contract_id: Contract ID

        Returns:
            True if contract has breaking changes, False otherwise
        """
        changelog = self.get_changelog(contract_id)
        return any(entry.get('breaking', False) for entry in changelog)

    def get_breaking_changes(self, contract_id: str) -> List[Dict[str, Any]]:
        """
        Get all breaking change entries from changelog.

        Args:
            contract_id: Contract ID

        Returns:
            List of changelog entries that are breaking changes
        """
        changelog = self.get_changelog(contract_id)
        return [entry for entry in changelog if entry.get('breaking', False)]

    def cleanup_old_versions(
        self,
        contract_id: str,
        keep_count: int = 10
    ) -> int:
        """
        Remove old version history, keeping only the most recent ones.

        Args:
            contract_id: Contract ID
            keep_count: Number of versions to keep (not including current)

        Returns:
            Number of versions deleted
        """
        contract = self.registry.get(contract_id)
        if not contract:
            return 0

        history_dir = self._get_history_dir(contract)
        if not history_dir.exists():
            return 0

        # Get all version files sorted by version
        version_files = []
        for file in history_dir.iterdir():
            if file.is_file() and file.suffix == '.json':
                version_str = file.stem
                try:
                    version = ContractVersion.from_string(version_str)
                    version_files.append((version, file))
                except (ValueError, IndexError):
                    continue

        # Sort by version (oldest first)
        version_files.sort(key=lambda x: (x[0].major, x[0].minor, x[0].patch))

        # Delete oldest versions beyond keep_count
        deleted_count = 0
        files_to_delete = version_files[:-keep_count] if len(version_files) > keep_count else []

        for _, file in files_to_delete:
            try:
                file.unlink()
                deleted_count += 1
            except IOError:
                continue

        return deleted_count
