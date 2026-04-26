from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor


def _shadow():
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(20)
    s.setOffset(0, 4)
    s.setColor(QColor(0, 0, 0, 100))
    return s


class ResultCard(QFrame):
    def __init__(self, title: str, body: str, note: str, accent: str, parent=None):
        super().__init__(parent)
        self.setObjectName("rc")
        self.setStyleSheet(f"""
            QFrame#rc {{
                background: #1e1e1e;
                border-radius: 14px;
                border-left: 4px solid {accent};
            }}
        """)
        self.setGraphicsEffect(_shadow())

        v = QVBoxLayout(self)
        v.setContentsMargins(24, 18, 24, 18)
        v.setSpacing(8)

        t = QLabel(title)
        t.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        t.setStyleSheet("color:#cccccc;")
        v.addWidget(t)

        if body:
            b = QLabel(body)
            b.setFont(QFont("Segoe UI", 11))
            b.setStyleSheet("color:#777777;")
            b.setWordWrap(True)
            v.addWidget(b)

        if note:
            n = QLabel(note)
            n.setFont(QFont("Segoe UI", 10))
            n.setStyleSheet("color:#444444; font-style:italic;")
            n.setWordWrap(True)
            v.addWidget(n)


class DiagnosisTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")

        self._inner = QWidget()
        self._inner.setStyleSheet("background:transparent;")
        self._lay = QVBoxLayout(self._inner)
        self._lay.setContentsMargins(36, 30, 36, 30)
        self._lay.setSpacing(14)

        h1 = QLabel("Диагностика")
        h1.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        h1.setStyleSheet("color:#fff;")
        self._lay.addWidget(h1)

        h2 = QLabel("Результаты тестирования и тренировок")
        h2.setFont(QFont("Segoe UI", 11))
        h2.setStyleSheet("color:#444;")
        self._lay.addWidget(h2)

        self._lay.addSpacing(8)

        self._lay.addStretch()
        scroll.setWidget(self._inner)
        root.addWidget(scroll)

    def add_result(self, source: str, data: str):
        self._lay.insertWidget(
            self._lay.count() - 1,
            ResultCard(
                title=f"Результат · {source}",
                body=data,
                note="",
                accent="#5B8DEF",
            )
        )
