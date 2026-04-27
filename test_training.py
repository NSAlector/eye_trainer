import sys
import time
from pathlib import Path

#sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from tabs.training_tab import TrainingTab

def main():
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("Training Tab Test")
    window.setGeometry(100, 100, 1920, 1200)
    
    training_tab = TrainingTab()
    test_plan = {
        "disease": "Deuteranopia",
        "level": "+1",
        "background": "star.json",
        "object_hex": "#FF0000",
        "object_scale": 1.0,
        "speed_ms": 2,
        "bl_type": "Deuteranopia",
        "exercises": [
            {"name": "circle_right", "speed": "slow"}
        ],
        "notes": ["Test exercise"]
    }
    training_tab.apply_plan(test_plan)
    
    window.setCentralWidget(training_tab)
    window.show()
    
    training_tab._launch_gymnastics()
    
    
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
