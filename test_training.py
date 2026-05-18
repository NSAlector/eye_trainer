import sys
import time
from pathlib import Path

#sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from tabs.training_tab.training_tab import TrainingTab


    # "circle_right": calc_cur_coordinates_circle_right,
    # "circle_left": calc_cur_coordinates_circle_left,
    # "diagonal_up": calc_cur_coordinates_diagonal_up,
    # "diagonal_down": calc_cur_coordinates_diagonal_down,
    # "horizontal": calc_cur_coordinates_hotizontal,
    # "vertical": calc_cur_coordinates_vertical,
    # "zigzag": calc_cur_coordinates_zigzag,
    # "clock": calc_cur_coordinates_clock,
    # "two_diagonals": calc_cur_coordinates_two_diagonals,
    # "rectangle": calc_cur_coordinates_rectangle,


def main():
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("Training Tab Test")
    window.setGeometry(100, 100, 1920, 1200)
    
    training_tab = TrainingTab()
    test_plan = {
            "disease": "Healthy",
            "scene": "butterfly",
            "bl_type": "Healthy",
            "object_scale": 1.0,
            "speed_factor": 1.0,
            "exercise_duration": 60,
            "exercises": [
                {"name": "rectangle", "speed": "slow"}
            ],
            "notes": ["This is a test plan for the training tab."]}
    training_tab.apply_plan(test_plan)
    
    window.setCentralWidget(training_tab)
    window.show()
    
    training_tab._launch_gymnastics()
    
    
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
