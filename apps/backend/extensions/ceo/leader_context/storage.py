"""
Leader Context Storage
======================

Provides file system-based storage for LeaderContext instances.
Supports saving, loading, listing, backup, and restore operations.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import LeaderContext
from .serializer import LeaderContextSerializer


class ContextStorage:
    """
    File system-based storage for LeaderContext.

    Stores context data as JSON files in a configurable storage directory.
    Supports automatic backup on save, manual backup, and restore operations.

    Attributes:
        project_path: Path to the project root directory
        storage_path: Path to the storage directory for context files
        backup_dir: Path to the backup directory
    """

    # Default storage directory relative to project path
    DEFAULT_STORAGE_DIR = ".planning/leader_context"

    # Backup subdirectory name
    BACKUP_SUBDIR = "backups"

    # File naming pattern
    CONTEXT_FILE_PATTERN = "context_phase_{phase}.json"

    # Backup file naming pattern (includes timestamp)
    BACKUP_FILE_PATTERN = "context_phase_{phase}_{timestamp}.json"

    def __init__(
        self,
        project_path: str,
        storage_dir: str = DEFAULT_STORAGE_DIR
    ):
        """
        Initialize ContextStorage.

        Args:
            project_path: Path to the project root directory
            storage_dir: Storage directory relative to project path
        """
        self.project_path = Path(project_path)
        self.storage_path = self.project_path / storage_dir
        self.backup_dir = self.storage_path / self.BACKUP_SUBDIR

    def _ensure_dirs(self) -> None:
        """Ensure storage and backup directories exist."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _get_context_file_path(self, phase: int) -> Path:
        """Get the file path for a context by phase number."""
        filename = self.CONTEXT_FILE_PATTERN.format(phase=phase)
        return self.storage_path / filename

    def _get_backup_file_path(self, phase: int) -> Path:
        """Get a new backup file path with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.BACKUP_FILE_PATTERN.format(phase=phase, timestamp=timestamp)
        return self.backup_dir / filename

    def save(self, context: LeaderContext) -> bool:
        """
        Save context to file with automatic backup.

        Creates a backup of the existing file (if any) before saving.
        Updates the updated_at timestamp before saving.

        Args:
            context: LeaderContext instance to save

        Returns:
            True if save was successful, False otherwise

        Raises:
            IOError: If file operations fail
        """
        try:
            self._ensure_dirs()

            file_path = self._get_context_file_path(context.phase)

            # Create automatic backup if file exists
            if file_path.exists():
                self._create_backup(context.phase)

            # Update the updated_at timestamp
            context.updated_at = datetime.now()

            # Serialize and write
            json_content = LeaderContextSerializer.to_json(context)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_content)

            return True

        except (IOError, OSError) as e:
            # Log error in production
            print(f"Error saving context: {e}")
            return False

    def load(self, phase: Optional[int] = None) -> Optional[LeaderContext]:
        """
        Load context from file.

        If phase is specified, loads that specific phase's context.
        If phase is None, loads the most recent context (highest phase number).

        Args:
            phase: Phase number to load, or None for latest

        Returns:
            LeaderContext instance if found, None otherwise
        """
        try:
            if phase is not None:
                file_path = self._get_context_file_path(phase)
                if not file_path.exists():
                    return None
            else:
                # Find the latest phase
                phases = self.list_phases()
                if not phases:
                    return None
                phase = max(phases)
                file_path = self._get_context_file_path(phase)

            with open(file_path, 'r', encoding='utf-8') as f:
                json_content = f.read()

            return LeaderContextSerializer.from_json(json_content)

        except (IOError, OSError, json.JSONDecodeError) as e:
            # Log error in production
            print(f"Error loading context: {e}")
            return None

    def list_phases(self) -> List[int]:
        """
        List all saved phase numbers.

        Returns:
            Sorted list of phase numbers that have saved contexts
        """
        if not self.storage_path.exists():
            return []

        phases = []
        pattern = "context_phase_"
        suffix = ".json"

        for file in self.storage_path.iterdir():
            if file.is_file() and file.name.startswith(pattern) and file.name.endswith(suffix):
                try:
                    # Extract phase number from filename
                    phase_str = file.name[len(pattern):-len(suffix)]
                    phase = int(phase_str)
                    phases.append(phase)
                except ValueError:
                    # Skip files with non-numeric phase values
                    continue

        return sorted(phases)

    def delete(self, phase: int) -> bool:
        """
        Delete a specific phase's context.

        Creates a backup before deletion.

        Args:
            phase: Phase number to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            file_path = self._get_context_file_path(phase)

            if not file_path.exists():
                return False

            # Create backup before deletion
            self._create_backup(phase)

            # Delete the file
            os.remove(file_path)

            return True

        except (IOError, OSError) as e:
            print(f"Error deleting context: {e}")
            return False

    def _create_backup(self, phase: int) -> Optional[str]:
        """
        Create a backup of the current context file.

        Args:
            phase: Phase number to backup

        Returns:
            Path to backup file if successful, None otherwise
        """
        try:
            source_path = self._get_context_file_path(phase)

            if not source_path.exists():
                return None

            self._ensure_dirs()
            backup_path = self._get_backup_file_path(phase)

            shutil.copy2(source_path, backup_path)

            return str(backup_path)

        except (IOError, OSError) as e:
            print(f"Error creating backup: {e}")
            return None

    def backup(self, context: LeaderContext) -> str:
        """
        Create a manual backup of a context.

        Unlike automatic backups during save, this creates a backup
        from the provided context object (not from an existing file).

        Args:
            context: LeaderContext instance to backup

        Returns:
            Path to backup file if successful, empty string otherwise
        """
        try:
            self._ensure_dirs()

            backup_path = self._get_backup_file_path(context.phase)
            json_content = LeaderContextSerializer.to_json(context)

            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(json_content)

            return str(backup_path)

        except (IOError, OSError) as e:
            print(f"Error creating manual backup: {e}")
            return ""

    def restore(self, backup_path: str) -> Optional[LeaderContext]:
        """
        Restore context from a backup file.

        Loads the context from the backup file and optionally saves it
        as the current context for that phase.

        Args:
            backup_path: Path to the backup file

        Returns:
            LeaderContext instance if successful, None otherwise
        """
        try:
            backup_file = Path(backup_path)

            if not backup_file.exists():
                print(f"Backup file not found: {backup_path}")
                return None

            with open(backup_file, 'r', encoding='utf-8') as f:
                json_content = f.read()

            context = LeaderContextSerializer.from_json(json_content)

            return context

        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"Error restoring from backup: {e}")
            return None

    def list_backups(self, phase: Optional[int] = None) -> List[str]:
        """
        List all backup files.

        Args:
            phase: If specified, only list backups for that phase

        Returns:
            List of backup file paths, sorted by timestamp (newest first)
        """
        if not self.backup_dir.exists():
            return []

        backups = []
        pattern_prefix = "context_phase_"

        for file in self.backup_dir.iterdir():
            if file.is_file() and file.name.startswith(pattern_prefix):
                if phase is not None:
                    # Check if this backup is for the specified phase
                    expected_prefix = f"context_phase_{phase}_"
                    if not file.name.startswith(expected_prefix):
                        continue
                backups.append(str(file))

        # Sort by modification time, newest first
        backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        return backups

    def cleanup_old_backups(self, keep_count: int = 5, phase: Optional[int] = None) -> int:
        """
        Remove old backups, keeping only the most recent ones.

        Args:
            keep_count: Number of backups to keep per phase
            phase: If specified, only clean up backups for that phase

        Returns:
            Number of backups deleted
        """
        deleted_count = 0

        if phase is not None:
            phases_to_clean = [phase]
        else:
            # Get all phases from backup filenames
            phases_to_clean = self._get_phases_from_backups()

        for p in phases_to_clean:
            backups = self.list_backups(phase=p)

            # Delete backups beyond keep_count
            for backup_path in backups[keep_count:]:
                try:
                    os.remove(backup_path)
                    deleted_count += 1
                except OSError:
                    continue

        return deleted_count

    def _get_phases_from_backups(self) -> List[int]:
        """Extract unique phase numbers from backup filenames."""
        if not self.backup_dir.exists():
            return []

        phases = set()
        pattern_prefix = "context_phase_"

        for file in self.backup_dir.iterdir():
            if file.is_file() and file.name.startswith(pattern_prefix):
                try:
                    # Extract phase from pattern: context_phase_{phase}_{timestamp}.json
                    name_parts = file.name[len(pattern_prefix):].split('_')
                    if name_parts:
                        phase = int(name_parts[0])
                        phases.add(phase)
                except (ValueError, IndexError):
                    continue

        return sorted(phases)

    def exists(self, phase: int) -> bool:
        """
        Check if a context exists for the given phase.

        Args:
            phase: Phase number to check

        Returns:
            True if context exists, False otherwise
        """
        file_path = self._get_context_file_path(phase)
        return file_path.exists()

    def get_storage_info(self) -> dict:
        """
        Get information about the storage.

        Returns:
            Dictionary with storage statistics
        """
        phases = self.list_phases()
        all_backups = self.list_backups()

        total_size = 0
        if self.storage_path.exists():
            for file in self.storage_path.rglob('*.json'):
                total_size += file.stat().st_size

        return {
            'storage_path': str(self.storage_path),
            'backup_path': str(self.backup_dir),
            'total_phases': len(phases),
            'phases': phases,
            'total_backups': len(all_backups),
            'total_size_bytes': total_size,
        }
