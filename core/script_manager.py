"""
ScriptManager – CRUD operations for scripts and execution history.

Persists scripts as individual JSON files in data/scripts/.
Persists execution history per-script in data/history/.
"""

from __future__ import annotations

import json
import os
import shutil
from typing import List, Optional

from core.models import ExecutionRecord, Script, ScriptHistory
from utils.constants import HISTORY_DIR, SCRIPTS_DIR
from utils.logger import get_logger

logger = get_logger("core.script_manager")


class ScriptManager:
    """Manages script persistence (save / load / delete / import / export)
    and execution history."""

    def __init__(self) -> None:
        os.makedirs(SCRIPTS_DIR, exist_ok=True)
        os.makedirs(HISTORY_DIR, exist_ok=True)
        logger.info("ScriptManager initialised (scripts=%s)", SCRIPTS_DIR)

    # -----------------------------------------------------------------------
    # Script CRUD
    # -----------------------------------------------------------------------

    def _script_path(self, name: str) -> str:
        safe = self._safe_filename(name)
        return os.path.join(SCRIPTS_DIR, f"{safe}.json")

    def _history_path(self, name: str) -> str:
        safe = self._safe_filename(name)
        return os.path.join(HISTORY_DIR, f"{safe}_history.json")

    @staticmethod
    def _safe_filename(name: str) -> str:
        """Sanitise a script name for use as a filename."""
        return "".join(c if c.isalnum() or c in " _-" else "_" for c in name).strip()

    def save_script(self, script: Script) -> None:
        """Save (or overwrite) a script to disk."""
        script.touch()
        path = self._script_path(script.name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(script.to_json())
        logger.info("Script saved: '%s' → %s", script.name, path)

    def load_script(self, name: str) -> Optional[Script]:
        """Load a script by name. Returns None if not found."""
        path = self._script_path(name)
        if not os.path.exists(path):
            logger.warning("Script not found: '%s'", name)
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Script loaded: '%s'", name)
        return Script.from_dict(data)

    def list_scripts(self) -> List[str]:
        """Return a sorted list of saved script names."""
        names = []
        for fname in os.listdir(SCRIPTS_DIR):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(SCRIPTS_DIR, fname), "r", encoding="utf-8") as f:
                        data = json.load(f)
                    names.append(data.get("name", fname[:-5]))
                except (json.JSONDecodeError, KeyError):
                    names.append(fname[:-5])
        return sorted(names)

    def delete_script(self, name: str) -> bool:
        """Delete a script and its history. Returns True if deleted."""
        path = self._script_path(name)
        deleted = False
        if os.path.exists(path):
            os.remove(path)
            deleted = True
            logger.info("Script deleted: '%s'", name)

        hist_path = self._history_path(name)
        if os.path.exists(hist_path):
            os.remove(hist_path)

        return deleted

    def rename_script(self, old_name: str, new_name: str) -> bool:
        """Rename a script. Returns True on success."""
        script = self.load_script(old_name)
        if script is None:
            return False

        # Rename script
        script.name = new_name
        self.save_script(script)

        # Move history
        old_hist = self._history_path(old_name)
        if os.path.exists(old_hist):
            history = self.load_history(old_name)
            history.script_name = new_name
            self._save_history(history, new_name)
            os.remove(old_hist)

        # Delete old script file
        old_path = self._script_path(old_name)
        if os.path.exists(old_path) and old_name != new_name:
            os.remove(old_path)

        logger.info("Script renamed: '%s' → '%s'", old_name, new_name)
        return True

    def script_exists(self, name: str) -> bool:
        return os.path.exists(self._script_path(name))

    # -----------------------------------------------------------------------
    # Import / Export
    # -----------------------------------------------------------------------

    def export_script(self, name: str, filepath: str) -> bool:
        """Export a script to an external file path."""
        src = self._script_path(name)
        if not os.path.exists(src):
            logger.warning("Export failed – script '%s' not found", name)
            return False
        shutil.copy2(src, filepath)
        logger.info("Script exported: '%s' → %s", name, filepath)
        return True

    def import_script(self, filepath: str) -> Optional[Script]:
        """Import a script from an external JSON file."""
        if not os.path.exists(filepath):
            logger.warning("Import failed – file not found: %s", filepath)
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            script = Script.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.error("Import failed – invalid script file: %s (%s)", filepath, exc)
            return None

        # Avoid name collisions
        base_name = script.name
        counter = 1
        while self.script_exists(script.name):
            script.name = f"{base_name} ({counter})"
            counter += 1

        self.save_script(script)
        logger.info("Script imported: '%s' from %s", script.name, filepath)
        return script

    # -----------------------------------------------------------------------
    # Execution History
    # -----------------------------------------------------------------------

    def load_history(self, script_name: str) -> ScriptHistory:
        """Load execution history for a script."""
        path = self._history_path(script_name)
        if not os.path.exists(path):
            return ScriptHistory(script_name=script_name)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ScriptHistory.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return ScriptHistory(script_name=script_name)

    def _save_history(self, history: ScriptHistory, name: str | None = None) -> None:
        path = self._history_path(name or history.script_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history.to_dict(), f, indent=2, ensure_ascii=False)

    def add_execution_record(self, record: ExecutionRecord) -> None:
        """Append an execution record to the script's history."""
        history = self.load_history(record.script_name)
        history.add(record)
        self._save_history(history)
        logger.info(
            "Execution record added: '%s' – %s (%.0f ms, %d actions)",
            record.script_name, record.status,
            record.duration_ms, record.actions_executed,
        )
