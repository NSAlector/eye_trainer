"""JSON-based data storage and retrieval utilities."""

import json
import os
from pathlib import Path
from typing import Optional

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "survey_results")


class JsonDataLoader:
    @staticmethod
    def load_profile(user_id: str) -> Optional[dict]:
        """Load a complete user profile from JSON by user_id (filename without extension)."""
        try:
            # user_id is the filename without extension
            # e.g., "john_doe_20260414_120530"
            filepath = os.path.join(RESULTS_DIR, f"{user_id}.json")
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            return data
        except Exception as e:
            print(f"[JsonDataLoader] Ошибка загрузки профиля: {e}")
            return None
    
    @staticmethod
    def load_exercise_plan(user_id: str) -> Optional[dict]:
        """Load an exercise plan from a user's JSON profile."""
        profile = JsonDataLoader.load_profile(user_id)
        if not profile:
            return None
        return profile.get("exercise_plan")
    
    @staticmethod
    def list_all_profiles() -> list:
        """List all saved user profiles."""
        try:
            if not os.path.exists(RESULTS_DIR):
                return []
            
            files = [f for f in os.listdir(RESULTS_DIR) if f.endswith(".json")]
            files.sort(key=lambda f: os.path.getmtime(os.path.join(RESULTS_DIR, f)))
            return [os.path.splitext(f)[0] for f in files]

        except Exception as e:
            print(f"[JsonDataLoader] Ошибка при получении списка профилей: {e}")
            return []
    
    @staticmethod
    def get_latest_profile() -> Optional[dict]:
        """Get the most recently saved profile."""
        try:
            profiles = JsonDataLoader.list_all_profiles()
            if not profiles:
                return None
            
            latest_user_id = profiles[-1]  # Last one (sorted)
            return JsonDataLoader.load_profile(latest_user_id)
        except Exception as e:
            print(f"[JsonDataLoader] Ошибка получения последнего профиля: {e}")
            return None
    
    @staticmethod
    def get_latest_exercise_plan() -> Optional[dict]:
        """Get the exercise plan from the most recently saved profile."""
        profile = JsonDataLoader.get_latest_profile()
        if not profile:
            return None
        return profile.get("exercise_plan")
