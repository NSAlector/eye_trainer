import json
import os


class SurveyLoader:
    def load(self, path: str) -> dict:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Survey file not found: {path}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def get_all_questions(self, survey: dict) -> list:
        questions = []
        for section in survey.get("sections", []):
            section_title = section.get("title", "")
            for q in section.get("questions", []):
                q["_section_title"] = section_title
                questions.append(q)
        return questions
