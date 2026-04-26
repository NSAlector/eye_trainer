import os
import sys
import subprocess
import mmap
import struct
import time
import json
import numpy as np
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from python_gaze.gaze_tracker import GazeTrackerRunner
from python_renderer.sharedMemoryFileWriter import SharedMemoryWriter
from tabs.validation import ExerciseValidator

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QPushButton, QFrame, QGridLayout,
    QGraphicsDropShadowEffect, QHBoxLayout, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QThread, QFile, QTimer
from PySide6.QtGui import QFont, QColor, QPixmap, QImage
from PySide6.QtUiTools import QUiLoader

class SharedMemoryReader:
    def __init__(self, name="frames"):
        self.name = name
        self.map_file = None
        self.fd = None
        self.last_frame_id = -1
        self.HEADER_SIZE = SharedMemoryWriter.HEADER_SIZE
        self.HEADER_FORMAT = SharedMemoryWriter.HEADER_FORMAT

    def _connect(self):
        if self.map_file:
            return True
        try:
            if sys.platform == "win32":
                tmp = mmap.mmap(-1, self.HEADER_SIZE, tagname=f"Local\\{self.name}")
                header = tmp.read(self.HEADER_SIZE)
                tmp.close()
                if len(header) < self.HEADER_SIZE:
                    return False
                counter, flag, w, h = struct.unpack(self.HEADER_FORMAT, header)
                if w == 0 or h == 0:
                    return False
                total_size = self.HEADER_SIZE + w * h * 3
                self.map_file = mmap.mmap(-1, total_size, tagname=f"Local\\{self.name}")
                self.last_frame_id = counter - 1
                return True
            else:
                path = f"/dev/shm/{self.name}"
                if not os.path.exists(path):
                    return False
                fd = os.open(path, os.O_RDONLY)
                header = os.read(fd, self.HEADER_SIZE)
                if len(header) < self.HEADER_SIZE:
                    os.close(fd)
                    return False
                counter, flag, w, h = struct.unpack(self.HEADER_FORMAT, header)
                if w == 0 or h == 0:
                    os.close(fd)
                    return False
                total_size = self.HEADER_SIZE + w * h * 3
                self.map_file = mmap.mmap(fd, total_size, mmap.MAP_SHARED, mmap.PROT_READ)
                self.fd = fd
                self.last_frame_id = counter - 1
                return True
        except Exception:
            return False

    def read_frame(self):
        if not self._connect():
            return None
        try:
            for _ in range(3):
                self.map_file.seek(0)
                header = self.map_file.read(self.HEADER_SIZE)
                counter, flag, w, h = struct.unpack(self.HEADER_FORMAT, header)
                if flag:
                    continue
                frame_size = w * h * 3
                self.map_file.seek(self.HEADER_SIZE)
                frame_data = self.map_file.read(frame_size)
                self.map_file.seek(0)
                header2 = self.map_file.read(self.HEADER_SIZE)
                counter2, _, _, _ = struct.unpack(self.HEADER_FORMAT, header2)
                if counter2 != counter:
                    continue
                if counter == self.last_frame_id:
                    return None
                self.last_frame_id = counter
                frame = np.frombuffer(frame_data, dtype=np.uint8)
                return frame.reshape((h, w, 3))
            return None
        except Exception:
            return None

    def close(self):
        if self.map_file:
            self.map_file.close()
            self.map_file = None
        if self.fd:
            os.close(self.fd)
            self.fd = None

class ProcessMonitorThread(QThread):
    finished_naturally = Signal()

    def __init__(self, process):
        super().__init__()
        self.process = process
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            if self.process.stderr:
                try:
                    self.process.stderr.readline()
                except Exception:
                    pass
            if self.process.stdout:
                try:
                    self.process.stdout.readline()
                except Exception:
                    pass
            if self.process.poll() is not None:
                if self.running:
                    self.finished_naturally.emit()
                break
            time.sleep(0.01)

    def stop(self):
        self.running = False
        self.quit()
        if not self.wait(3000):
            self.terminate()
            self.wait()

class FrameReaderThread(QThread):
    frameReady = Signal(QPixmap)

    def __init__(self):
        super().__init__()
        self.reader = SharedMemoryReader("frames")
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            frame = self.reader.read_frame()
            if frame is None:
                time.sleep(0.01)
                continue
            try:
                h, w = frame.shape[:2]
                if not frame.flags['C_CONTIGUOUS']:
                    frame = np.ascontiguousarray(frame)
                qt_image = QImage(frame.data, w, h, 3 * w, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image.copy())
                if not pixmap.isNull():
                    self.frameReady.emit(pixmap)
            except Exception:
                pass
            time.sleep(0.002)
        self.reader.close()

    def stop(self):
        self.running = False
        self.quit()
        if not self.wait(3000):
            self.terminate()
            self.wait()

def _shadow(blur=24, dy=6, alpha=80):
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur)
    s.setOffset(0, dy)
    s.setColor(QColor(0, 0, 0, alpha))
    return s

class ParamCard(QFrame):
    def __init__(self, label: str, value: str, accent: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setStyleSheet("""
            QFrame { background: #1e1e1e; border-radius: 10px; border: none; }
        """)
        self.setGraphicsEffect(_shadow(16, 4, 60))
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 16, 0)
        row.setSpacing(14)
        strip = QFrame()
        strip.setFixedWidth(3)
        strip.setMinimumHeight(80)
        strip.setStyleSheet(f"background: {accent}; border-radius: 2px; border: none;")
        row.addWidget(strip)
        col = QVBoxLayout()
        col.setSpacing(4)
        col.setContentsMargins(0, 12, 0, 12)
        lbl = QLabel(label.upper())
        lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {accent}; letter-spacing: 1.5px; background: transparent;")
        col.addWidget(lbl)
        val = QLabel(value)
        val.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        val.setStyleSheet("color: #ffffff; background: transparent;")
        col.addWidget(val)
        row.addLayout(col)

class ExerciseCard(QFrame):
    SPEED_LABELS = {
        "very_slow":("Очень медленно", "#7C5CBF"),
        "slow":("Медленно", "#5B8DEF"),
        "medium":("Стандартно", "#3DB87A")
    }
    EXERCISE_LABELS = {
        "circle_right":"Круг по часовой",
        "circle_left":"Круг против часовой",
        "horizontal":"Горизонталь",
        "vertical":"Вертикаль",
        "zigzag":"Зигзаг",
        "clock":"Циферблат",
        "two_diagonals":"Диагонали",
        "diagonal_up":"Диагональ вверх",
        "diagonal_down":"Диагональ вниз",
        "rectangle":"Прямоугольник",
    }

    def __init__(self, exercise: dict, index: int, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        speed = exercise.get("speed", "medium")
        name = exercise.get("name", "")
        label, color = self.SPEED_LABELS.get(speed, ("Стандартно", "#3DB87A"))
        ex_label = self.EXERCISE_LABELS.get(name, name)
        self.setStyleSheet("QFrame { background: #181818; border-radius: 10px; }")
        row = QHBoxLayout(self)
        row.setContentsMargins(16, 0, 16, 0)
        row.setSpacing(12)
        num = QLabel(f"{index:02d}")
        num.setFixedWidth(28)
        num.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        num.setStyleSheet(f"color: {color}; background: transparent;")
        row.addWidget(num)
        name_lbl = QLabel(ex_label)
        name_lbl.setFont(QFont("Segoe UI", 11))
        name_lbl.setStyleSheet("color: #cccccc; background: transparent;")
        row.addWidget(name_lbl, stretch=1)
        speed_lbl = QLabel(label)
        speed_lbl.setFont(QFont("Segoe UI", 9))
        speed_lbl.setStyleSheet(f"""
            color: {color}; background: {color}22; border-radius: 6px; padding: 3px 10px;
        """)
        row.addWidget(speed_lbl)

class LaunchButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(52)
        self.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton { background: #6C63FF; color: #ffffff; border: none; border-radius: 12px; letter-spacing: 1px; }
            QPushButton:hover { background: #574fd6; }
            QPushButton:pressed { background: #4840b8; }
            QPushButton:disabled { background: #222; color: #444; }
        """)
        self.setGraphicsEffect(_shadow(20, 6, 100))

class TrainingTab(QWidget):
    SCENE_RU = {
        "boat": "Катер", "bubble": "Пузырек", "bug": "Жук", "butterfly": "Бабочка",
        "mouse": "Мышонок", "plane": "Самолет", "star": "Звезда",
    }
    BL_RU = {
        "Healthy": "Нет нарушений", "Deuteranopia": "Дейтеранопия",
        "Protanopia": "Протанопия", "Tritanopia": "Тританопия", "Achromatopsia": "Ахроматопсия",
    }
    DISEASE_RU = { "myopia": "Миопия", "hyperopia": "Гиперметропия" }
    SPEED_MAP = {
        "very_slow": 0.3,
        "slow": 0.6,
        "medium": 1.0
    }
    training_finished = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._exercise_plan = {}
        self._current_user_id = None
        self._frame_reader_thread = None
        self._process_monitor_thread = None
        self._renderer_process = None
        self._current_ex_index = 0
        self._tracker = GazeTrackerRunner(width=1280, height=720)
        self._load_ui()

    def _load_ui(self):
        loader = QUiLoader()
        loader.registerCustomWidget(LaunchButton)
        ui_path = Path(__file__).resolve().parent / "training_tab.ui"
        ui_file = QFile(str(ui_path))
        ui_file.open(QFile.OpenModeFlag.ReadOnly)
        ui_widget = loader.load(ui_file, self)
        ui_file.close()
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(ui_widget)
        def w(cls, name): return ui_widget.findChild(cls, name)
        self._video_frame = w(QFrame, "videoFrame")
        self._video_label = w(QLabel, "videoLabel")
        self._stop_btn = w(LaunchButton, "stopBtn")
        self._title = w(QLabel, "titleLabel")
        self._subtitle = w(QLabel, "subtitleLabel")
        self._launch_btn = w(LaunchButton, "launchBtn")
        self._params_frame = w(QFrame, "paramsFrame")
        self._params_grid = w(QGridLayout, "paramsGrid")
        self._exercises_frame = w(QFrame, "exercisesFrame")
        self._ex_count = w(QLabel, "exCountLabel")
        self._exercises_lay = w(QVBoxLayout, "exercisesListLayout")
        self.scrollArea = w(QScrollArea, "scrollArea")
        self._ui_root = ui_widget
        self._launch_btn.clicked.connect(self._launch_gymnastics)
        self._stop_btn.clicked.connect(self._stop_training)

    def apply_plan(self, plan: dict, user_id: int = None):
        self._exercise_plan = plan
        self._current_user_id = user_id
        disease = plan.get("disease", "")
        level = plan.get("level", "")
        scene_id = plan.get("scene", "star")
        bl_type = plan.get("bl_type", "Healthy")
        disease_ru = self.DISEASE_RU.get(disease, disease.capitalize())
        scene_ru = self.SCENE_RU.get(scene_id, scene_id)
        bl_ru = self.BL_RU.get(bl_type, "Норма")
        if disease and disease != "healthy":
            self._subtitle.setText(f"Персональный план  ·  {disease_ru}  {level}")
        self._clear_grid()
        params = [("Диагноз", f"{disease_ru} {level}", "#5B8DEF"), ("Сцена", scene_ru, "#7C5CBF"), ("Цветовое зрение", bl_ru, "#48CAE4")]
        for i, (label, value, accent) in enumerate(params):
            self._params_grid.addWidget(ParamCard(label, value, accent), 0, i)
        self._params_frame.setVisible(True)
        self._clear_exercises()
        exercises = plan.get("exercises", [])
        self._ex_count.setText(f"{len(exercises)} упражнений")
        for i, ex in enumerate(exercises, 1):
            self._exercises_lay.addWidget(ExerciseCard(ex, i))
        self._exercises_frame.setVisible(bool(exercises))

    def _clear_grid(self):
        while self._params_grid.count():
            item = self._params_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def _clear_exercises(self):
        while self._exercises_lay.count():
            item = self._exercises_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def _get_plan(self):
        return self._exercise_plan or {"scene": "star", "object_scale": 1.0, "speed_ms": 30}

    def _launch_gymnastics(self):
        if hasattr(self, "_first_frame_received"): del self._first_frame_received
        self._current_ex_index = 0
        if hasattr(self, '_tracker'):
            self._tracker.start()
        self._start_next_exercise()

    def _start_next_exercise(self):
        if self._renderer_process:
            self._stop_renderer_only()
        plan = self._get_plan()
        exercises = plan.get("exercises", [])
        if self._current_ex_index >= len(exercises):
            self._stop_training()
            return
        exercise = exercises[self._current_ex_index]
        exercise_name = exercise.get("name", "circle_right")
        bl_type = plan.get("bl_type", "Healthy")
        raw_scene = plan.get("background") or plan.get("scene") or "star"
        object_scale = plan.get("object_scale", 1.0)
        scene = str(raw_scene).replace(".json", "").replace(".png", "")
        base_speed = self.SPEED_MAP.get(exercise.get("speed"), 1.0)
        duration = plan.get("exercise_duration", 30)
        multiplier = plan.get("speed_factor", 1.0)
        final_speed = round(base_speed * multiplier, 2)
        print(f"[TrainingTab] exercise={exercise_name}, base={base_speed}, factor={multiplier}, final={final_speed}")
        PROJECT_ROOT = Path(__file__).resolve()
        while not (PROJECT_ROOT / "python_renderer").exists() and PROJECT_ROOT.parent != PROJECT_ROOT:
            PROJECT_ROOT = PROJECT_ROOT.parent
        renderer_dir = PROJECT_ROOT / "python_renderer"
        renderer_script = renderer_dir / "renderer.py"
        python_exe = sys.executable

        args = [str(python_exe), str(renderer_script), "1", str(bl_type),
                str(exercise_name), str(scene), str(final_speed), "1280", "720",
                str(object_scale), str(duration)]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root_path)
        self._renderer_process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(renderer_dir), env=env)
        self._video_frame.setVisible(True)
        self.scrollArea.setVisible(False)
        root_layout = self._ui_root.layout()
        root_layout.setStretch(0, 1)
        root_layout.setStretch(1, 0)
        self._process_monitor_thread = ProcessMonitorThread(self._renderer_process)
        self._process_monitor_thread.finished_naturally.connect(self._on_exercise_finished)
        self._process_monitor_thread.start()
        if not self._frame_reader_thread or not self._frame_reader_thread.isRunning():
            self._frame_reader_thread = FrameReaderThread()
            self._frame_reader_thread.frameReady.connect(self._update_frame)
            self._frame_reader_thread.start()

    def _on_exercise_finished(self):
        self._current_ex_index += 1
        QTimer.singleShot(600, self._start_next_exercise)

    def _update_frame(self, pixmap: QPixmap):
        if pixmap.isNull(): return
        h = self._video_label.height()
        if h > 0: pixmap = pixmap.scaledToHeight(h, Qt.SmoothTransformation)
        self._video_label.setPixmap(pixmap)

    def _stop_renderer_only(self):
        if self._renderer_process:
            try:
                self._renderer_process.terminate()
                self._renderer_process.wait(timeout=1)
            except Exception:
                try: self._renderer_process.kill()
                except Exception: pass
            self._renderer_process = None

    def _stop_training(self):
        self._current_ex_index = 0

        if self._process_monitor_thread:
            try:
                self._process_monitor_thread.finished_naturally.disconnect()
            except Exception:
                pass
            self._process_monitor_thread.stop()
            self._process_monitor_thread = None

        if self._renderer_process:
            try:
                self._renderer_process.terminate()
                self._renderer_process.wait(timeout=2)
            except Exception:
                try: self._renderer_process.kill()
                except Exception: pass
            self._renderer_process = None

        if self._frame_reader_thread:
            self._frame_reader_thread.stop()
            self._frame_reader_thread = None

        gaze_data = self._tracker.stop()

        self._analyze_results(gaze_data)

        self._video_label.clear()
        self.scrollArea.setVisible(True)
        root_layout = self._ui_root.layout()
        root_layout.setStretch(0, 0)
        root_layout.setStretch(1, 1)

    def _analyze_results(self, gaze_data):
        PROJECT_ROOT = Path(__file__).resolve()
        while not (PROJECT_ROOT / "python_renderer").exists() and PROJECT_ROOT.parent != PROJECT_ROOT:
            PROJECT_ROOT = PROJECT_ROOT.parent
        log_path = PROJECT_ROOT / "data" / "gymnastics.log"
        try:
            target_data = []
            if log_path.exists():
                with open(log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            d = json.loads(line)
                            if d.get("levelname") == "INFO":
                                target_data.append({'duration': d['duration'], 'x_coord': d['x_coord'], 'y_coord': d['y_coord']})
                        except Exception: continue
            if not target_data or not gaze_data: return
            GROUND_SIZE, W, H = 12.0 * 0.85, 1280, 720
            for p in target_data:
                p['x_coord'] = int((p['x_coord'] / GROUND_SIZE + 1.0) * 0.5 * W)
                p['y_coord'] = int((p['y_coord'] / GROUND_SIZE + 1.0) * 0.5 * H)
            validator = ExerciseValidator(threshold=175.0, window_size=10)
            report = validator.validate(target_data, gaze_data)
            self.training_finished.emit(report)
        except Exception as e:
               print(f"[TrainingTab] analysis error: {e}")
               self.training_finished.emit(default_report)

    def _update_frame(self, pixmap: QPixmap):
            if pixmap.isNull():
                return

            if self._current_ex_index == 0 and not hasattr(self, "_first_frame_received"):
                self._tracker.start_time = time.time()
                self._tracker.history = []
                self._first_frame_received = True
                print("[TrainingTab] First frame received, tracker time synchronized!")

            h = self._video_label.height()
            if h > 0:
                pixmap = pixmap.scaledToHeight(h, Qt.SmoothTransformation)
            self._video_label.setPixmap(pixmap)

    def _cleanup(self):
        try: self._stop_training()
        except Exception: pass

    def closeEvent(self, event):
        self._cleanup()
        super().closeEvent(event)
