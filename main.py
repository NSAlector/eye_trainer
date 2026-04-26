"""
Eye Trainer Application - Main Entry Point

A comprehensive eye training application with:
- Survey/testing module for diagnosis
- Results and progress tracking
- Personalized training plan generation and execution

All logic is integrated in Python using PySide6 GUI framework.
"""
import sys
sys.path.insert(0, r'C:\Qt\eye_gymnastics2')
import multiprocessing
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

# Import tabs
from tabs.testing_tab.testing_tab import TestingTab
from tabs.diagnosis_tab import DiagnosisTab
from tabs.training_tab.training_tab import TrainingTab
from utils.result_processor import ResultProcessor

# Application-wide stylesheet
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

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.tab_testing = TestingTab()
        self.tab_diagnosis = DiagnosisTab()
        self.tab_training = TrainingTab()

        self.tabs.addTab(self.tab_testing, "  Тестирование  ")
        self.tabs.addTab(self.tab_diagnosis, "  Диагностика   ")
        self.tabs.addTab(self.tab_training, "  Тренировка    ")

        self.tab_training.training_finished.connect(self._on_training_finished)
        self.setCentralWidget(self.tabs)

        self.tab_testing.survey_finished.connect(self._on_survey_finished)
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _on_survey_finished(self, survey_result):
        try:
            result = self._processor.process(survey_result)
            
            self.tab_diagnosis.add_result(
                source="Первичный опрос",
                data=result["summary"],
            )
            
            plan = result["exercise_plan"]
            self.tab_training.apply_plan(plan)
            
            QTimer.singleShot(50, lambda: self.tabs.setCurrentIndex(1))
            
        except Exception as e:
            self._show_error(f"Ошибка при обработке результатов теста: {str(e)}")

    def _on_training_finished(self, report):
        score = report['score']
        avg_error = report['avg_error']
        anomalies = report.get('anomalies', [])
        timeline = report.get('timeline', [])

        if score >= 75:
            status = "Отлично"
        elif score >= 50:
            status = "Хорошо"
        else:
            status = "Нужно больше практики"

        lines = [
            f"Результат: {status}",
            f"Точность: {score}%",
            f"Средняя ошибка: {avg_error} px",
        ]

        if anomalies:
            lines.append(f"Потеря взгляда: {len(anomalies)} раз(а)")
            for seg in anomalies:
                lines.append(f"  • {seg[0]:.1f}с — {seg[1]:.1f}с")
        else:
            lines.append("Потеря взгляда: не обнаружена")

        if timeline:
            lines.append("\nДинамика по времени:")
            for item in timeline[::2]:  # каждые 2 секунды
                bar = "+" if item['error'] <= self.tab_training._exercise_plan.get('threshold', 175) else "-"
                lines.append(f"  {bar} {item['interval']}: {item['error']} px")

        self.tab_diagnosis.add_result(
            source="Анализ тренировки",
            data="\n".join(lines)
        )
        self.tabs.setCurrentIndex(1)

    def _on_tab_changed(self, index):
        pass

    def _show_error(self, message: str):
        QMessageBox.critical(self, "Ошибка", message)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.tab_training._cleanup()
        super().closeEvent(event)



if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    app = QApplication(sys.argv)
    
    app.setStyle("Fusion")
    
    window = EyeTrainerApp()
    window.show()
    
    sys.exit(app.exec())
