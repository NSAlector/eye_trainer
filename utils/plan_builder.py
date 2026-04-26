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

SIZE_MAP = {
    "medium": 1.0,
    "large": 1.5,
    "extra_large": 2.2
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
    speed_factor: float = 1.0
    exercise_duration: int = 30
    exercises: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "disease": self.disease,
            "level": self.level,
            "scene": self.scene,
            "bl_type": self.bl_type,
            "object_scale": self.object_scale,
            "speed_factor": self.speed_factor,
            "exercise_duration": self.exercise_duration,
            "exercises": self.exercises,
            "notes": self.notes,
        }


class PlanBuilder:
    def __init__(self):
        self._loader = ConfigLoader()

    def build(self, user_id: Optional[int], survey_answers: dict) -> ExercisePlan:
        print("[PlanBuilder] answers:", survey_answers)
        disease, level = self._detect_disease(survey_answers)
        bl_type = self._detect_bl_type(survey_answers)
        scene = self._choose_scene(survey_answers)

        config = self._loader.load(disease, level)

        plan = ExercisePlan(
            user_id=user_id,
            disease=disease,
            level=level,
            config=None,
            scene=scene,
            bl_type=bl_type
        )

        if config:
            plan.object_scale = SIZE_MAP.get(config.object.size, 1.0)

            plan.exercises = [
                {"name": ex.name, "speed": ex.speed}
                for ex in config.exercises
            ]

            plan.exercise_duration = config.exercise_duration
        else:
            plan = self._default_plan(user_id, disease, level, scene, bl_type)

        fatigue = self._get_answer(survey_answers, "q_fatigue", "medium")

        if fatigue == "high":
            plan.speed_factor = 0.7

            if len(plan.exercises) > 3:
                plan.exercises = plan.exercises[:3]

        elif fatigue == "low":
            plan.speed_factor = 1.3

        print(f"[PlanBuilder] speed_factor={plan.speed_factor}, exercises={plan.exercises}")  # <--

        return plan

    def _detect_disease(self, answers: dict) -> tuple:
        disease = self._get_answer(answers, "q_disease_type", "none")
        if disease in ("none", "healthy", "other"):
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
        interests = answers.get("q_theme", [])
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
