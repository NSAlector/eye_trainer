from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QCheckBox, QRadioButton, QButtonGroup, QLineEdit, QLabel
)
from PySide6.QtCore import Signal
from .ui_testing_tab import Ui_Form as Ui_TestingTab
from .ui_control_panel import Ui_Form as Ui_ControlPanel
from utils.data_loader import SurveyLoader
from utils.result_processor import SurveyResult, SurveyAnswer

SKIP_LEVEL_FOR = {"other", ""}


class TestingTab(QWidget):
    survey_finished = Signal(object)

    def __init__(self):
        super().__init__()

        self.ui = Ui_TestingTab()
        self.ui.setupUi(self)

        self.control_widget = QWidget()
        self.cp = Ui_ControlPanel()
        self.cp.setupUi(self.control_widget)

        self.cp.horizontalLayoutWidget.setParent(None)
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.addWidget(self.cp.btnPrev)
        nav_layout.addWidget(self.cp.btnNext)
        nav_layout.addWidget(self.cp.btnFinish)
        self.control_widget.setLayout(nav_layout)
        self.control_widget.setFixedHeight(48)

        self.ui.mainLayout.addWidget(self.control_widget)
        self.control_widget.setVisible(False)

        self.questions = []
        self.current_idx = 0
        self.answers = {}
        self.button_group = None
        self._survey_id = ""
        self._text_input = None

        self.ui.groupBox.setVisible(False)
        self.ui.labelProgress.setVisible(False)
        self.ui.progressBar.setVisible(False)

        self.ui.btnStart.clicked.connect(self._on_start)
        self.cp.btnPrev.clicked.connect(self._on_prev)
        self.cp.btnNext.clicked.connect(self._on_next)
        self.cp.btnFinish.clicked.connect(self._on_finish)

    def _should_skip(self, q: dict) -> bool:
        skip_if = q.get("skip_if")
        if skip_if:
            dep_qid = skip_if.get("question_id")
            skip_values = skip_if.get("values", [])
            for ans in self.answers.values():
                if ans.question_id == dep_qid:
                    if ans.answer and ans.answer[0] in skip_values:
                        return True
                    break

        options_if = q.get("options_if")
        if options_if:
            opts = self._get_options(q)
            if not opts:
                return True

        return False

    def _get_options(self, q: dict) -> list:
        options_if = q.get("options_if")
        if options_if:
            for dep_qid, mapping in options_if.items():
                for ans in self.answers.values():
                    if ans.question_id == dep_qid and ans.answer:
                        chosen = ans.answer[0]
                        if chosen in mapping:
                            return mapping[chosen]
            return []
        raw = q.get("options", [])
        return raw

    def _next_valid_idx(self, from_idx: int, direction: int = 1) -> int:
        idx = from_idx + direction
        while 0 <= idx < len(self.questions):
            if not self._should_skip(self.questions[idx]):
                return idx
            idx += direction
        return idx

    def _visible_count(self) -> int:
        return sum(1 for q in self.questions if not self._should_skip(q))

    def _visible_position(self) -> int:
        pos = 0
        for i, q in enumerate(self.questions):
            if not self._should_skip(q):
                pos += 1
            if i == self.current_idx:
                return pos
        return pos

    def _on_start(self):
        loader = SurveyLoader()
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent
        abs_survey_path = project_root / "tests" / "test_data" / "example_test.json"

        if not abs_survey_path.exists():
            print(f"[TestingTab] Файл с тестом не найден: {abs_survey_path}")
            self.ui.labelQuestion.setText(f"Ошибка: Файл с вопросами не найден!\n{abs_survey_path}")
            return

        survey = loader.load(str(abs_survey_path))

        self._survey_id = survey.get("survey_info", {}).get("survey_id", "unknown")
        self.questions = loader.get_all_questions(survey)
        self.current_idx = 0
        self.answers = {}

        if not self.questions:
            self.ui.labelQuestion.setText("Нет вопросов в тесте!")
            return

        if self._should_skip(self.questions[0]):
            self.current_idx = self._next_valid_idx(-1, 1)

        self.ui.btnStart.setVisible(False)
        self.ui.groupBox.setVisible(True)
        self.ui.labelProgress.setVisible(True)
        self.ui.progressBar.setVisible(True)
        self.control_widget.setVisible(True)
        self._show_question()

    def _on_prev(self):
        self._save_answer()
        idx = self._next_valid_idx(self.current_idx, -1)
        if 0 <= idx < len(self.questions):
            self.current_idx = idx
            self._show_question()

    def _on_next(self):
        self._save_answer()
        idx = self._next_valid_idx(self.current_idx, 1)
        if 0 <= idx < len(self.questions):
            self.current_idx = idx
            self._show_question()

    def _on_finish(self):
        self._save_answer()
        self._finish()

    def _show_question(self):
        q = self.questions[self.current_idx]
        total = self._visible_count()
        pos = self._visible_position()

        self.ui.progressBar.setValue(int((pos / total) * 100))
        self.ui.labelProgress.setText(f"Вопрос {pos} из {total}")
        self.ui.labelTitle.setText(q.get("_section_title", ""))
        self.ui.labelQuestion.setText(q.get("text", ""))

        next_idx = self._next_valid_idx(self.current_idx, 1)
        prev_idx = self._next_valid_idx(self.current_idx, -1)
        has_next = 0 <= next_idx < len(self.questions)
        has_prev = 0 <= prev_idx < len(self.questions)

        self.cp.btnPrev.setEnabled(has_prev)
        self.cp.btnNext.setVisible(has_next)
        self.cp.btnFinish.setVisible(not has_next)

        self._clear_answers()

        q_type = q.get("type", "single_choice")
        options = self._get_options(q)
        opts = [o["text"] if isinstance(o, dict) else o for o in options]
        saved = self.answers.get(self.current_idx)

        if q_type == "text":
            self._build_text_input(saved)
        elif q_type == "boolean":
            self._build_radio(["Да", "Нет"], saved.answer if saved else [])
        elif q_type == "multiple_choice":
            self._build_checkboxes(opts, saved.answer if saved else [])
        else:
            self._build_radio(opts, saved.answer if saved else [])

    def _build_text_input(self, saved=None):
        self._text_input = QLineEdit()
        self._text_input.setPlaceholderText("Введите ответ...")
        if saved and saved.answer:
            self._text_input.setText(saved.answer[0])
        self.ui.answersLayout.addWidget(self._text_input)
        self.ui.answersLayout.addStretch()

    def _build_radio(self, options, saved):
        self.button_group = QButtonGroup(self)
        for i, opt in enumerate(options):
            rb = QRadioButton(opt)
            if opt in saved:
                rb.setChecked(True)
            self.button_group.addButton(rb, i)
            self.ui.answersLayout.addWidget(rb)
        self.ui.answersLayout.addStretch()

    def _build_checkboxes(self, options, saved):
        self.button_group = None
        for opt in options:
            cb = QCheckBox(opt)
            if opt in saved:
                cb.setChecked(True)
            self.ui.answersLayout.addWidget(cb)
        self.ui.answersLayout.addStretch()

    def _clear_answers(self):
        layout = self.ui.answersLayout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.button_group = None
        self._text_input  = None

    def _save_answer(self):
        q = self.questions[self.current_idx]
        q_type = q.get("type", "single_choice")

        if q_type == "text" and self._text_input:
            text = self._text_input.text().strip()
            selected = [text] if text else []
        else:
            layout = self.ui.answersLayout
            selected = []

            raw_opts = self._get_options(q)
            text_to_value = {}
            for o in raw_opts:
                if isinstance(o, dict) and "value" in o:
                    text_to_value[o.get("text", "")] = o["value"]

            for i in range(layout.count()):
                item = layout.itemAt(i)
                if not item:
                    continue
                w = item.widget()
                if isinstance(w, (QRadioButton, QCheckBox)) and w.isChecked():
                    txt = w.text()
                    selected.append(text_to_value.get(txt, txt))

        self.answers[self.current_idx] = SurveyAnswer(
            question_id = q.get("question_id", f"q_{self.current_idx}"),
            question_text = q.get("text", ""),
            answer = selected,
        )

    def _finish(self):
        all_answers = []
        for idx, ans in self.answers.items():
            if idx < len(self.questions):
                if not self._should_skip(self.questions[idx]):
                    all_answers.append(ans)

        result = SurveyResult(
            survey_id = self._survey_id,
            answers = all_answers,
        )
        self.survey_finished.emit(result)

        self.ui.progressBar.setValue(100)
        self.ui.labelProgress.setText("Тест завершён!")
        self.ui.labelTitle.setText("Спасибо за прохождение теста.")
        self.ui.labelQuestion.setText("")
        self._clear_answers()
        self.ui.groupBox.setVisible(False)
        self.control_widget.setVisible(False)
        self.ui.btnStart.setText("Пройти ещё раз")
        self.ui.btnStart.setVisible(True)
