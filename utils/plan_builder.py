import random
from dataclasses import dataclass, field
from typing import Optional
from .config_loader import ConfigLoader, DiseaseConfig

DISEASE_KEYWORDS = {
    "myopia":["миопия", "близорукость", "myopia"],
    "hyperopia":["гиперметропия", "дальнозоркость", "hyperopia"],
}

MYOPIA_LEVELS = {"-1", "-2", "-3", "-4", "-5", "-6"}
HYPEROPIA_LEVELS = {"+1", "+2", "+3", "+4", "+5", "+6"}

SCENE_MAP = {
        "nature": ["butterfly", "bug"],
        "transport": ["plane", "boat"],
        "space": ["star", "plane"],
        "animals": ["mouse"],
        "sea": ["bubble", "boat"]
}

DEFAULT_SCENE = "star"

@dataclass
class ExercisePlan:
    user_id: Optional[int]
    disease: str
    level: str
    config: Optional[DiseaseConfig]
    scene: str = DEFAULT_SCENE
    bl_type: str = "Healthy"
    object_scale: float = 1.0
    speed_ms: float = 2.0
    exercises: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "disease": self.disease,
            "level": self.level,
            "scene": self.scene,
            "bl_type": self.bl_type,
            "object_scale": self.object_scale,
            "speed_ms": self.speed_ms,
            "exercises": self.exercises,
            "notes": self.notes,
        }


class PlanBuilder:
    def __init__(self):
        self._loader = ConfigLoader()

    def build(self, user_id: Optional[int], survey_answers: dict) -> ExercisePlan:
        disease, level = self._detect_disease(survey_answers)
        bl_type = self._detect_bl_type(survey_answers)
        scene = self._choose_scene(survey_answers)
        config = self._loader.load(disease, level)

        plan = ExercisePlan(user_id=user_id, disease=disease, level=level, config=config, scene=scene, bl_type=bl_type, )

        if config:
            plan.object_scale = config.object_scale
            plan.speed_ms = config.speed_ms
            plan.exercises = [{"name": e.name, "speed": e.speed} for e in config.exercises]
        else:
            plan = self._default_plan(user_id, disease, level, scene, bl_type)

        return plan

    def _detect_disease(self, answers: dict) -> tuple:
        disease = self._get_answer(answers, "q_disease_type", "other")
        if disease not in ("myopia", "hyperopia"):
            return "healthy", "0"

        level = self._get_answer(answers, "q_disease_level", "")
        valid = MYOPIA_LEVELS if disease == "myopia" else HYPEROPIA_LEVELS

        if level not in valid:
            level = "-1" if disease == "myopia" else "+1"
        return disease, level

    @staticmethod
    def _detect_bl_type(answers: dict) -> str:
        valid = {"Healthy", "Deuteranopia", "Protanopia", "Tritanopia", "Achromatopsia"}
        bl = answers.get("q_color_blindness", ["Healthy"])
        val = bl[0] if bl else "Healthy"
        return val if val in valid else "Healthy"

    @staticmethod
    def _choose_scene(answers: dict) -> str:
        interests = answers.get("q_int_001", [])
        possible = []
        for key in interests:
            possible.extend(SCENE_MAP.get(key, []))
        possible = list(set(possible))
        return random.choice(possible) if possible else DEFAULT_SCENE


    @staticmethod
    def _default_plan(user_id, disease, level, scene, bl_type) -> ExercisePlan:
        return ExercisePlan(
            user_id=user_id, disease=disease, level=level, config=None, scene=scene, bl_type=bl_type,
            exercises=[
                {"name": "circle_right", "speed": "medium"},
                {"name": "horizontal", "speed": "medium"},
                {"name": "vertical", "speed": "medium"},
            ],
            notes=["Стандартная программа"],
        )

    @staticmethod
    def _get_answer(answers: dict, key: str, default: str = "") -> str:
        val = answers.get(key,[])
        return val[0] if val else default
