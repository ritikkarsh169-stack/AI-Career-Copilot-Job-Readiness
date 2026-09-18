"""DataStorage — save and load UserProfile to/from a JSON file."""

import json
import os
from typing import Optional

from career_copilot.models.profile import UserProfile

DEFAULT_SAVE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "user_profile.json"
)


class DataStorage:
    """
    Handles JSON persistence for a single UserProfile.

    Usage:
        storage = DataStorage()          # uses default path
        storage.save(profile)
        profile = storage.load()         # returns None if no data saved yet
    """

    def __init__(self, filepath: Optional[str] = None) -> None:
        self._filepath: str = os.path.normpath(
            filepath if filepath else DEFAULT_SAVE_PATH
        )

    @property
    def filepath(self) -> str:
        return self._filepath

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(self, profile: UserProfile) -> None:
        """Serialise a UserProfile and write it to the JSON file."""
        os.makedirs(os.path.dirname(self._filepath), exist_ok=True)
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)

    def load(self) -> Optional[UserProfile]:
        """
        Read the JSON file and return a UserProfile.
        Returns None if the file doesn't exist.
        Raises ValueError if the file is corrupted or contains invalid data.
        """
        if not os.path.exists(self._filepath):
            return None

        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"The save file '{self._filepath}' is corrupted and cannot be read. "
                f"Details: {exc}"
            ) from exc

        try:
            return UserProfile.from_dict(data)
        except (KeyError, ValueError) as exc:
            raise ValueError(
                f"The save file contains invalid profile data. Details: {exc}"
            ) from exc

    def delete(self) -> None:
        """Remove the save file if it exists."""
        if os.path.exists(self._filepath):
            os.remove(self._filepath)
