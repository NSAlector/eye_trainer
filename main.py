import sys
import multiprocessing
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PySide6.QtCore import Qt
from tabs.testing_tab.testing_tab import TestingTab
from tabs.diagnosis_tab import DiagnosisTab
from tabs.training_tab import TrainingTab
from utils.result_processor import ResultProcessor

STYLE = """
* {
    font-family: 'Bahnschrift';
}

QMainWindow, QWidget {
    background-color: #141414;
    color: #ffffff;
}

QTabWidget::pane {
    border: none;
    background-color: #141414;
}

QTabBar {
    background: #1a1a1a;
}

QTabBar::tab {
    background-color: #1a1a1a;
    color: #555555;
    font-size: 15px;
    font-weight: 600;
    padding: 16px 36px;
    border: none;
    border-bottom: 3px solid transparent;
    min-width: 160px;
}

QTabBar::tab:selected {
    color: #ffffff;
    background-color: #141414;
    border-bottom: 3px solid #5B8DEF;
}

QTabBar::tab:hover:!selected {
    color: #aaaaaa;
    background-color: #1f1f1f;
}

QPushButton {
    background-color: #5B8DEF;
    color: white;
    border: none;
    padding: 10px 24px;
    margin: 4px;
    border-radius: 6px;
    font-weight: 500;
    font-size: 14px;
}

QPushButton:hover { background-color: #4a7de0; }
QPushButton:disabled { background-color: #2a2a2a; color: #444; }

QGroupBox {
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    margin-top: 8px;
    padding-top: 8px;
}

QGroupBox::title {
    color: #555;
    subcontrol-origin: margin;
    left: 12px;
}

QProgressBar {
    background-color: #1a1a1a;
    border: none;
    border-radius: 4px;
}

QProgressBar::chunk {
    background-color: #5B8DEF;
    border-radius: 4px;
}

QLineEdit {
    background: #1e1e1e;
    color: #ffffff;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 16px;
}

QRadioButton, QCheckBox {
    font-size: 16px;
    spacing: 12px;
    padding: 6px 0px;
    color: #eeeeee;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    background-color: #1a1a1a;
    border: 2px solid #555555;
}

QRadioButton::indicator {
    border-radius: 11px;
}

QCheckBox::indicator {
    border-radius: 4px;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #5B8DEF;
}

QCheckBox::indicator:checked {
    background-color: #5B8DEF;
    border-color: #5B8DEF;
}

QRadioButton::indicator:checked {
    background-color: #5B8DEF;
    border: 5px solid #1a1a1a;
}
"""


class EyeTrainerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EyeTrainer")
        self.showMaximized()
        self.setStyleSheet(STYLE)

        self._processor = ResultProcessor()
        self._current_user_id = None

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.tab_testing = TestingTab()
        self.tab_diagnosis = DiagnosisTab()
        self.tab_training = TrainingTab()

        self.tabs.addTab(self.tab_testing, "  Тестирование  ")
        self.tabs.addTab(self.tab_diagnosis, "  Диагностика   ")
        self.tabs.addTab(self.tab_training, "  Тренировка    ")

        self.setCentralWidget(self.tabs)

        self.tab_testing.survey_finished.connect(self._on_survey_finished)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.tab_training.training_finished.connect(self._on_training_finished)

    def _on_survey_finished(self, survey_result):
        result = self._processor.process(survey_result)

        self._current_user_id = result.get("user_id")

        self.tab_diagnosis.add_result(
            source="Первичный опрос",
            data=result["summary"],
        )

        plan = result["exercise_plan"]
        self.tab_training.apply_plan(plan, self._current_user_id)

        self.tabs.setCurrentIndex(1)

    def _on_tab_changed(self, index):
        if index == 2 and self._current_user_id:
            if not self.tab_training._exercise_plan:
                self.tab_training.load_plan_from_db(self._current_user_id)

    def _on_training_finished(self, report):
        status = "Успешно" if report['is_success'] else "Требуется повторение"

        report_text = (
            f"Оценка точности: {report['score']}/100\n"
            f"Средняя ошибка: {report['avg_error']} px\n"
            f"Результат: {status}\n"
            f"Участков потери фокуса: {len(report['anomalies'])}"
        )

        self.tab_diagnosis.add_result(
            source="Анализ гимнастики",
            data=report_text
        )
        self.tabs.setCurrentIndex(1)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.tab_training._cleanup()
        super().closeEvent(event)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    window = EyeTrainerApp()
    sys.exit(app.exec())
