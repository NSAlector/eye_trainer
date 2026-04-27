import os
import yaml
from dataclasses import dataclass, field
from typing import Optional


CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")


@dataclass
class ColorCombo:
    object_color: str
    background: str
    background_hex: str
    background_file: str


@dataclass
class ObjectParams:
    size: str

@dataclass
class ExerciseParams:
    name: str
    speed: str


@dataclass
class DiseaseConfig:
    disease: str
    level: str
    colors: list
    object: ObjectParams
    exercises: list

    @property
    def primary_color(self) -> ColorCombo:
        return self.colors[0] if self.colors else ColorCombo(
            "белый", "#FFFFFF", "белый", "#FFFFFF", "star"
        )

    @property
    def speed_ms(self) -> float:
        """Скорость в мс для таймера упражнения"""
        return {"very_slow": 0.3, "slow": 0.5, "medium": 2.0}.get(
            self.exercises[0].speed if self.exercises else "medium", 2.0
        )

    @property
    def object_scale(self) -> float:
        """Масштаб объекта"""
        return {"medium": 1.0, "large": 1.4, "extra_large": 1.8}.get(
            self.object.size, 1.0
        )


class ConfigLoader:
    _cache: dict = {}

    def load(self, disease: str, level: str) -> Optional[DiseaseConfig]:
        key = f"{disease}_{level}"
        if key in self._cache:
            return self._cache[key]

        filename = f"{disease}_{level}.yaml"
        path = os.path.join(CONFIG_DIR, disease, filename)

        if not os.path.exists(path):
            print(f"[ConfigLoader] файл не найден: {path}")
            return None

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        colors = [
            ColorCombo(
                object_color = c.get("object_color", ""),
                background = c.get("background", ""),
                background_hex = c.get("background_hex", "#FFFFFF"),
                background_file = c.get("background_file", "star"),
            )
            for c in data.get("color_combinations", [])
            if c.get("recommended", False)
        ]

        obj_raw = data.get("object", {})
        obj = ObjectParams(
            size = obj_raw.get("size", "medium"),
        )

        exercises = [
            ExerciseParams(
                name = e.get("name", "circle_right"),
                speed = e.get("speed", "medium"),
            )
            for e in data.get("exercises", [])
        ]

        config = DiseaseConfig(
            disease = data.get("disease", disease),
            level = str(data.get("level", level)),
            colors = colors,
            object = obj,
            exercises = exercises,
        )
        self._cache[key] = config
        return config

    def available_levels(self, disease: str) -> list:
        levels = []
        if not os.path.exists(CONFIG_DIR):
            return levels
        disease_dir = os.path.join(CONFIG_DIR, disease)
        if not os.path.exists(disease_dir):
            return levels
        for f in os.listdir(disease_dir):
            if f.startswith(disease) and f.endswith(".yaml"):
                level = f.replace(f"{disease}_", "").replace(".yaml", "")
                levels.append(level)
        return sorted(levels)
