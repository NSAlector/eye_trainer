# import os
# import sys
# import subprocess
# import mmap
# import struct
# import time
# import json
# import numpy as np
# from pathlib import Path

# root_path = Path(__file__).resolve().parent.parent.parent
# if str(root_path) not in sys.path:
#     sys.path.append(str(root_path))

# #from python_gaze.gaze_tracker import GazeTrackerRunner
# from utils.sharedMemoryFileWriter import SharedMemoryWriter
# from tabs.validation import ExerciseValidator

# from PySide6.QtWidgets import (
#     QWidget, QVBoxLayout, QLabel, QScrollArea,
#     QPushButton, QFrame, QGridLayout,
#     QGraphicsDropShadowEffect, QHBoxLayout, QSizePolicy,
# )
# from PySide6.QtCore import Qt, Signal, QThread, QFile, QTimer
# from PySide6.QtGui import QFont, QColor, QPixmap, QImage
# from PySide6.QtUiTools import QUiLoader


# class ProcessMonitorThread(QThread):
#     finished_naturally = Signal()

#     def __init__(self, process):
#         super().__init__()
#         self.process = process
#         self.running = False

#     def run(self):
#         self.running = True
#         while self.running:
#             if self.process.stderr:
#                 try:
#                     self.process.stderr.readline()
#                 except Exception:
#                     pass
#             if self.process.stdout:
#                 try:
#                     self.process.stdout.readline()
#                 except Exception:
#                     pass
#             if self.process.poll() is not None:
#                 if self.running:
#                     self.finished_naturally.emit()
#                 break
#             time.sleep(0.01)

#     def stop(self):
#         self.running = False
#         self.quit()
#         if not self.wait(3000):
#             self.terminate()
#             self.wait()

# class FrameReaderThread(QThread):
#     frameReady = Signal(QPixmap)

#     def __init__(self):
#         super().__init__()
#         self.reader = SharedMemoryReader("frames")
#         self.running = False

#     def run(self):
#         self.running = True
#         while self.running:
#             frame = self.reader.read_frame()
#             if frame is None:
#                 time.sleep(0.01)
#                 continue
#             try:
#                 h, w = frame.shape[:2]
#                 if not frame.flags['C_CONTIGUOUS']:
#                     frame = np.ascontiguousarray(frame)
#                 qt_image = QImage(frame.data, w, h, 3 * w, QImage.Format.Format_RGB888)
#                 pixmap = QPixmap.fromImage(qt_image.copy())
#                 if not pixmap.isNull():
#                     self.frameReady.emit(pixmap)
#             except Exception:
#                 pass
#             time.sleep(0.002)
#         self.reader.close()

#     def stop(self):
#         self.running = False
#         self.quit()
#         if not self.wait(3000):
#             self.terminate()
#             self.wait()

# def _shadow(blur=24, dy=6, alpha=80):
#     s = QGraphicsDropShadowEffect()
#     s.setBlurRadius(blur)
#     s.setOffset(0, dy)
#     s.setColor(QColor(0, 0, 0, alpha))
#     return s

# class ParamCard(QFrame):
#     def __init__(self, label: str, value: str, accent: str, parent=None):
#         super().__init__(parent)
#         self.setFixedHeight(80)
#         self.setStyleSheet("""
#             QFrame { background: #1e1e1e; border-radius: 10px; border: none; }
#         """)
#         self.setGraphicsEffect(_shadow(16, 4, 60))
#         row = QHBoxLayout(self)
#         row.setContentsMargins(0, 0, 16, 0)
#         row.setSpacing(14)
#         strip = QFrame()
#         strip.setFixedWidth(3)
#         strip.setMinimumHeight(80)
#         strip.setStyleSheet(f"background: {accent}; border-radius: 2px; border: none;")
#         row.addWidget(strip)
#         col = QVBoxLayout()
#         col.setSpacing(4)
#         col.setContentsMargins(0, 12, 0, 12)
#         lbl = QLabel(label.upper())
#         lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
#         lbl.setStyleSheet(f"color: {accent}; letter-spacing: 1.5px; background: transparent;")
#         col.addWidget(lbl)
#         val = QLabel(value)
#         val.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
#         val.setStyleSheet("color: #ffffff; background: transparent;")
#         col.addWidget(val)
#         row.addLayout(col)

# class ExerciseCard(QFrame):
#     SPEED_LABELS = {
#         "very_slow":("Очень медленно", "#7C5CBF"),
#         "slow":("Медленно", "#5B8DEF"),
#         "medium":("Стандартно", "#3DB87A")
#     }
#     EXERCISE_LABELS = {
#         "circle_right":"Круг по часовой",
#         "circle_left":"Круг против часовой",
#         "horizontal":"Горизонталь",
#         "vertical":"Вертикаль",
#         "zigzag":"Зигзаг",
#         "clock":"Циферблат",
#         "two_diagonals":"Диагонали",
#         "diagonal_up":"Диагональ вверх",
#         "diagonal_down":"Диагональ вниз",
#         "rectangle":"Прямоугольник",
#     }

#     def __init__(self, exercise: dict, index: int, parent=None):
#         super().__init__(parent)
#         self.setFixedHeight(56)
#         speed = exercise.get("speed", "medium")
#         name = exercise.get("name", "")
#         label, color = self.SPEED_LABELS.get(speed, ("Стандартно", "#3DB87A"))
#         ex_label = self.EXERCISE_LABELS.get(name, name)
#         self.setStyleSheet("QFrame { background: #181818; border-radius: 10px; }")
#         row = QHBoxLayout(self)
#         row.setContentsMargins(16, 0, 16, 0)
#         row.setSpacing(12)
#         num = QLabel(f"{index:02d}")
#         num.setFixedWidth(28)
#         num.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
#         num.setStyleSheet(f"color: {color}; background: transparent;")
#         row.addWidget(num)
#         name_lbl = QLabel(ex_label)
#         name_lbl.setFont(QFont("Segoe UI", 11))
#         name_lbl.setStyleSheet("color: #cccccc; background: transparent;")
#         row.addWidget(name_lbl, stretch=1)
#         speed_lbl = QLabel(label)
#         speed_lbl.setFont(QFont("Segoe UI", 9))
#         speed_lbl.setStyleSheet(f"""
#             color: {color}; background: {color}22; border-radius: 6px; padding: 3px 10px;
#         """)
#         row.addWidget(speed_lbl)

# class LaunchButton(QPushButton):
#     def __init__(self, text: str = "", parent=None):
#         super().__init__(text, parent)
#         self.setFixedHeight(52)
#         self.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
#         self.setCursor(Qt.CursorShape.PointingHandCursor)
#         self.setStyleSheet("""
#             QPushButton { background: #6C63FF; color: #ffffff; border: none; border-radius: 12px; letter-spacing: 1px; }
#             QPushButton:hover { background: #574fd6; }
#             QPushButton:pressed { background: #4840b8; }
#             QPushButton:disabled { background: #222; color: #444; }
#         """)
#         self.setGraphicsEffect(_shadow(20, 6, 100))

# class TrainingTab(QWidget):
#     SCENE_RU = {
#         "boat": "Катер", "bubble": "Пузырек", "bug": "Жук", "butterfly": "Бабочка",
#         "mouse": "Мышонок", "plane": "Самолет", "star": "Звезда",
#     }
#     BL_RU = {
#         "Healthy": "Нет нарушений", "Deuteranopia": "Дейтеранопия",
#         "Protanopia": "Протанопия", "Tritanopia": "Тританопия", "Achromatopsia": "Ахроматопсия",
#     }
#     DISEASE_RU = { "myopia": "Миопия", "hyperopia": "Гиперметропия" }
#     SPEED_MAP = {
#         "very_slow": 0.3,
#         "slow": 0.6,
#         "medium": 1.0
#     }
#     training_finished = Signal(dict)

#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self._exercise_plan = {}
#         self._current_user_id = None
#         self._frame_reader_thread = None
#         self._process_monitor_thread = None
#         self._renderer_process = None
#         self._current_ex_index = 0
#         #self._tracker = GazeTrackerRunner(width=1280, height=720)
#         self._load_ui()

#     def _load_ui(self):
#         loader = QUiLoader()
#         loader.registerCustomWidget(LaunchButton)
#         ui_path = Path(__file__).resolve().parent / "training_tab.ui"
#         ui_file = QFile(str(ui_path))
#         ui_file.open(QFile.OpenModeFlag.ReadOnly)
#         ui_widget = loader.load(ui_file, self)
#         ui_file.close()
#         root_layout = QVBoxLayout(self)
#         root_layout.setContentsMargins(0, 0, 0, 0)
#         root_layout.setSpacing(0)
#         root_layout.addWidget(ui_widget)
#         def w(cls, name): return ui_widget.findChild(cls, name)
#         self._video_frame = w(QFrame, "videoFrame")
#         self._video_frame = w(QLabel, "videoLabel")
#         self._stop_btn = w(LaunchButton, "stopBtn")
#         self._title = w(QLabel, "titleLabel")
#         self._subtitle = w(QLabel, "subtitleLabel")
#         self._launch_btn = w(LaunchButton, "launchBtn")
#         self._params_frame = w(QFrame, "paramsFrame")
#         self._params_grid = w(QGridLayout, "paramsGrid")
#         self._exercises_frame = w(QFrame, "exercisesFrame")
#         self._ex_count = w(QLabel, "exCountLabel")
#         self._exercises_lay = w(QVBoxLayout, "exercisesListLayout")
#         self.scrollArea = w(QScrollArea, "scrollArea")
#         self._ui_root = ui_widget
#         self._launch_btn.clicked.connect(self._launch_gymnastics)
#         self._stop_btn.clicked.connect(self._stop_training)

#     def apply_plan(self, plan: dict, user_id: int = None):
#         self._exercise_plan = plan
#         self._current_user_id = user_id
#         disease = plan.get("disease", "")
#         level = plan.get("level", "")
#         scene_id = plan.get("scene", "star")
#         bl_type = plan.get("bl_type", "Healthy")
#         disease_ru = self.DISEASE_RU.get(disease, disease.capitalize())
#         scene_ru = self.SCENE_RU.get(scene_id, scene_id)
#         bl_ru = self.BL_RU.get(bl_type, "Норма")
#         if disease and disease != "healthy":
#             self._subtitle.setText(f"Персональный план  ·  {disease_ru}  {level}")
#         self._clear_grid()
#         params = [("Диагноз", f"{disease_ru} {level}", "#5B8DEF"), ("Сцена", scene_ru, "#7C5CBF"), ("Цветовое зрение", bl_ru, "#48CAE4")]
#         for i, (label, value, accent) in enumerate(params):
#             self._params_grid.addWidget(ParamCard(label, value, accent), 0, i)
#         self._params_frame.setVisible(True)
#         self._clear_exercises()
#         exercises = plan.get("exercises", [])
#         self._ex_count.setText(f"{len(exercises)} упражнений")
#         for i, ex in enumerate(exercises, 1):
#             self._exercises_lay.addWidget(ExerciseCard(ex, i))
#         self._exercises_frame.setVisible(bool(exercises))

#     def _clear_grid(self):
#         while self._params_grid.count():
#             item = self._params_grid.takeAt(0)
#             if item.widget(): item.widget().deleteLater()

#     def _clear_exercises(self):
#         while self._exercises_lay.count():
#             item = self._exercises_lay.takeAt(0)
#             if item.widget(): item.widget().deleteLater()

#     def _get_plan(self):
#         return self._exercise_plan or {"scene": "star", "object_scale": 1.0, "speed_ms": 30}

#     def _launch_gymnastics(self):
#         if hasattr(self, "_first_frame_received"): del self._first_frame_received
#         self._current_ex_index = 0
#         if hasattr(self, '_tracker'):
#             self._tracker.start()
#         self._start_next_exercise()

#     def _start_next_exercise(self):
#         if self._renderer_process:
#             self._stop_renderer_only()
#         plan = self._get_plan()
#         exercises = plan.get("exercises", [])
#         if self._current_ex_index >= len(exercises):
#             self._stop_training()
#             return
#         exercise = exercises[self._current_ex_index]
#         exercise_name = exercise.get("name", "circle_right")
#         bl_type = plan.get("bl_type", "Healthy")
#         raw_scene = plan.get("background") or plan.get("scene") or "star"
#         object_scale = plan.get("object_scale", 1.0)
#         scene = str(raw_scene).replace(".json", "").replace(".png", "")
#         base_speed = self.SPEED_MAP.get(exercise.get("speed"), 1.0)
#         duration = plan.get("exercise_duration", 30)
#         multiplier = plan.get("speed_factor", 1.0)
#         final_speed = round(base_speed * multiplier, 2)
#         print(f"[TrainingTab] exercise={exercise_name}, base={base_speed}, factor={multiplier}, final={final_speed}")
#         PROJECT_ROOT = Path(__file__).resolve()
#         while not (PROJECT_ROOT / "python_renderer").exists() and PROJECT_ROOT.parent != PROJECT_ROOT:
#             PROJECT_ROOT = PROJECT_ROOT.parent
#         renderer_dir = PROJECT_ROOT / "python_renderer"
#         renderer_script = renderer_dir / "renderer.py"
#         python_exe = sys.executable

#         args = [str(python_exe), str(renderer_script), "1", str(bl_type),
#                 str(exercise_name), str(scene), str(final_speed), "1280", "720",
#                 str(object_scale), str(duration)]
#         env = os.environ.copy()
#         env["PYTHONPATH"] = str(root_path)
#         self._renderer_process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(renderer_dir), env=env)
#         self._video_frame.setVisible(True)
#         self.scrollArea.setVisible(False)
#         root_layout = self._ui_root.layout()
#         root_layout.setStretch(0, 1)
#         root_layout.setStretch(1, 0)
#         self._process_monitor_thread = ProcessMonitorThread(self._renderer_process)
#         self._process_monitor_thread.finished_naturally.connect(self._on_exercise_finished)
#         self._process_monitor_thread.start()
#         if not self._frame_reader_thread or not self._frame_reader_thread.isRunning():
#             self._frame_reader_thread = FrameReaderThread()
#             self._frame_reader_thread.frameReady.connect(self._update_frame)
#             self._frame_reader_thread.start()

#     def _on_exercise_finished(self):
#         self._current_ex_index += 1
#         QTimer.singleShot(600, self._start_next_exercise)

#     def _update_frame(self, pixmap: QPixmap):
#         if pixmap.isNull(): return
#         h = self._video_frame.height()
#         if h > 0: pixmap = pixmap.scaledToHeight(h, Qt.SmoothTransformation)
#         self._video_frame.setPixmap(pixmap)

#     def _stop_renderer_only(self):
#         if self._renderer_process:
#             try:
#                 self._renderer_process.terminate()
#                 self._renderer_process.wait(timeout=1)
#             except Exception:
#                 try: self._renderer_process.kill()
#                 except Exception: pass
#             self._renderer_process = None

#     def _stop_training(self):
#         self._current_ex_index = 0

#         if self._process_monitor_thread:
#             try:
#                 self._process_monitor_thread.finished_naturally.disconnect()
#             except Exception:
#                 pass
#             self._process_monitor_thread.stop()
#             self._process_monitor_thread = None

#         if self._renderer_process:
#             try:
#                 self._renderer_process.terminate()
#                 self._renderer_process.wait(timeout=2)
#             except Exception:
#                 try: self._renderer_process.kill()
#                 except Exception: pass
#             self._renderer_process = None

#         if self._frame_reader_thread:
#             self._frame_reader_thread.stop()
#             self._frame_reader_thread = None

#         #gaze_data = self._tracker.stop()

#         #self._analyze_results(gaze_data)

#         self._video_frame.clear()
#         self.scrollArea.setVisible(True)
#         root_layout = self._ui_root.layout()
#         root_layout.setStretch(0, 0)
#         root_layout.setStretch(1, 1)

#     # def _analyze_results(self, gaze_data):
#     #     PROJECT_ROOT = Path(__file__).resolve()
#     #     while not (PROJECT_ROOT / "python_renderer").exists() and PROJECT_ROOT.parent != PROJECT_ROOT:
#     #         PROJECT_ROOT = PROJECT_ROOT.parent
#     #     log_path = PROJECT_ROOT / "data" / "gymnastics.log"
#     #     try:
#     #         target_data = []
#     #         if log_path.exists():
#     #             with open(log_path, "r", encoding="utf-8") as f:
#     #                 for line in f:
#     #                     try:
#     #                         d = json.loads(line)
#     #                         if d.get("levelname") == "INFO":
#     #                             target_data.append({'duration': d['duration'], 'x_coord': d['x_coord'], 'y_coord': d['y_coord']})
#     #                     except Exception: continue
#     #         if not target_data or not gaze_data: return
#     #         GROUND_SIZE, W, H = 12.0 * 0.85, 1280, 720
#     #         for p in target_data:
#     #             p['x_coord'] = int((p['x_coord'] / GROUND_SIZE + 1.0) * 0.5 * W)
#     #             p['y_coord'] = int((p['y_coord'] / GROUND_SIZE + 1.0) * 0.5 * H)
#     #         validator = ExerciseValidator(threshold=175.0, window_size=10)
#     #         report = validator.validate(target_data, gaze_data)
#     #         self.training_finished.emit(report)
#     #     except Exception as e:
#     #            print(f"[TrainingTab] analysis error: {e}")
#     #            self.training_finished.emit(default_report)

#     def _update_frame(self, pixmap: QPixmap):
#             if pixmap.isNull():
#                 return

#             if self._current_ex_index == 0 and not hasattr(self, "_first_frame_received"):
#                 self._tracker.start_time = time.time()
#                 self._tracker.history = []
#                 self._first_frame_received = True
#                 print("[TrainingTab] First frame received, tracker time synchronized!")

#             h = self._video_frame.height()
#             if h > 0:
#                 pixmap = pixmap.scaledToHeight(h, Qt.SmoothTransformation)
#             self._video_frame.setPixmap(pixmap)

#     def _cleanup(self):
#         try: self._stop_training()
#         except Exception: pass

#     def closeEvent(self, event):
#         self._cleanup()
#         super().closeEvent(event)


import mmap 
import os
from datetime import datetime, time
import sys
import json
import time
import random
import traceback
from PIL import Image
import cv2
import numpy as np
import struct
import subprocess
from pathlib import Path
import threading
from hypergan_api import HyPERGANTransform

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QGridLayout,
    QGraphicsDropShadowEffect, QSizePolicy, QGraphicsScene,
    QGraphicsPixmapItem, QGraphicsView
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont, QColor, QPixmap, QImage
from python_renderer import renderer
from utils.sharedMemoryFileWriter import SharedMemoryWriter
from utils.sharedMemoryFileReader import SharedMemoryReader
from tabs.validation import ExerciseValidator
    

class ProcessMonitorThread(QThread):
    finished_naturally = Signal()

    def __init__(self, process):
        super().__init__()
        self.process = process
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            if self.process.poll() is not None:
                if self.running:
                    self.finished_naturally.emit()
                break
            time.sleep(0.1)

    def stop(self):
        self.running = False
        self.wait(2000)


class FrameReaderThread(QThread):
    frameReady = Signal(QPixmap)

    def __init__(self):
        super().__init__()
        self.reader = SharedMemoryReader("frames")
        self.running = False
        self._hypergan = HyPERGANTransform(
            repo_path="/home/felix/repo/tmp/eye-trainer-working/HyPER-GAN",
            checkpoint_path="/home/felix/repo/tmp/eye-trainer-working/HyPER-GAN/pretrained_models/gta2cs.pth",
            input_size=512,
        )
        
        self.frame_counter = 0

    def run(self):
        self.running = True
        print("[FrameReaderThread] Started")
        
        while self.running:
            frame = self.reader.read_frame()
            
            if frame is None:
                time.sleep(0.001)
                continue
            
            if not frame.flags['C_CONTIGUOUS']:
                frame = np.ascontiguousarray(frame)
            
            if frame is not None and frame.size > 0:
                try:
                    output = self._hypergan.transform(frame)
                    #print(f"[FrameReaderThread] Frame transformed successfully (shape: {output.shape})")
                    
                    if output is not None:
                        h, w = output.shape[:2]
                        bytes_per_line = 3 * w
                        qimage = QImage(output.data, w, h, bytes_per_line, QImage.Format_RGB888)
                        pixmap = QPixmap.fromImage(qimage)
                        self.frameReady.emit(pixmap)
                        
                        self.frame_counter += 1
                    else:
                        print("[FrameReaderThread] Frame transformation returned None")
                        
                except Exception as e:
                    print(f"[FrameReaderThread] Error: {e}")
                    import traceback
                    traceback.print_exc()
        
        if self.reader:
            self.reader.close()
        print("[FrameReaderThread] Stopped")

    def stop(self):
        self.running = False
        self.wait(5000)


class CameraRecorderThread(QThread):
    recording_started = Signal()
    recording_error = Signal(str)

    def __init__(self, output_path: str = None):
        super().__init__()
        self.running = False
        self.cap = None
        self.writer = None
        self.output_path = output_path or self._get_default_output_path()
        self.fps = 30
        self.frame_width = 640
        self.frame_height = 480
        self.frame_count = 0

    def _get_default_output_path(self) -> str:
        from datetime import datetime as dt
        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
        data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "videos"
        data_dir.mkdir(parents=True, exist_ok=True)
        return str(data_dir / f"camera_recording_{timestamp}.avi")

    def _init_video_writer(self):
        import platform
        
        codecs = []
        if platform.system() == "Linux":
            codecs = [
                ('MJPG', 'avi'),
                ('XVID', 'avi'),
                ('WMV1', 'avi'),
            ]
        elif platform.system() == "Darwin":
            codecs = [
                ('mp4v', 'mp4'),
                ('avc1', 'mp4'),
                ('MJPG', 'avi'),
            ]
        else:  
            codecs = [
                ('mp4v', 'mp4'),
                ('XVID', 'avi'),
                ('MJPG', 'avi'),
            ]

        for codec_code, ext in codecs:
            try:
                fourcc = cv2.VideoWriter_fourcc(*codec_code)
                output_path = self.output_path.rsplit('.', 1)[0] + f'.{ext}'
                
                writer = cv2.VideoWriter(
                    output_path,
                    fourcc,
                    self.fps,
                    (self.frame_width, self.frame_height)
                )
                
                if writer.isOpened():
                    print(f"[CameraRecorderThread] Using codec: {codec_code} with extension: {ext}")
                    self.output_path = output_path
                    return writer
            except Exception as e:
                print(f"[CameraRecorderThread] Codec {codec_code} failed: {e}")
                continue

        raise RuntimeError("No suitable video codec found")

    def run(self):
        self.running = True
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.recording_error.emit("Failed to open camera")
                return

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

            self.writer = self._init_video_writer()

            if not self.writer or not self.writer.isOpened():
                self.recording_error.emit(f"Failed to open video writer at {self.output_path}")
                if self.cap:
                    self.cap.release()
                return

            print(f"[CameraRecorderThread] Started recording to {self.output_path}")
            self.recording_started.emit()

            frame_skip = 0
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("[CameraRecorderThread] Failed to read frame from camera")
                    import time as time_module
                    time_module.sleep(0.01)
                    continue

                if frame.shape[1] != self.frame_width or frame.shape[0] != self.frame_height:
                    frame = cv2.resize(frame, (self.frame_width, self.frame_height))

                self.writer.write(frame)
                self.frame_count += 1
                
                if self.frame_count % 1 == 0:
                    try:
                        _ = self.writer.get(cv2.CAP_PROP_FRAME_COUNT)
                    except:
                        pass
                
                import time as time_module
                time_module.sleep(1.0 / self.fps)

        except Exception as e:
            self.recording_error.emit(f"Camera recording error: {str(e)}")
            print(f"[CameraRecorderThread] Error: {e}")
            traceback.print_exc()
        finally:
            self._cleanup()
            print(f"[CameraRecorderThread] Stopped (recorded {self.frame_count} frames)")

    def _cleanup(self):
        self.writer = None
        
        if self.cap:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None

    def stop(self):
        self.running = False
        self.wait(3000)


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
            QFrame {
                background: #1e1e1e;
                border-radius: 10px;
                border: none;
            }
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
        "very_slow": ("Очень медленно", "#7C5CBF"),
        "slow": ("Медленно", "#5B8DEF"),
        "medium": ("Стандартно", "#3DB87A"),
    }
    EXERCISE_LABELS = {
        "circle_right": "Круг по часовой",
        "circle_left": "Круг против часовой",
        "horizontal": "Горизонталь",
        "vertical": "Вертикаль",
        "zigzag": "Зигзаг",
        "clock": "Циферблат",
        "two_diagonals": "Диагонали",
        "diagonal_up": "Диагональ вверх",
        "diagonal_down": "Диагональ вниз",
        "rectangle": "Прямоугольник",
    }

    def __init__(self, exercise: dict, index: int, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)

        speed = exercise.get("speed", "medium")
        name = exercise.get("name", "")
        label, color = self.SPEED_LABELS.get(speed, ("Стандартно", "#3DB87A"))
        ex_label = self.EXERCISE_LABELS.get(name, name)

        self.setStyleSheet("""
            QFrame {
                background: #181818;
                border-radius: 10px;
            }
        """)

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
            color: {color};
            background: {color}22;
            border-radius: 6px;
            padding: 3px 10px;
        """)
        row.addWidget(speed_lbl)


class LaunchButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(52)
        self.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5B8DEF, stop:1 #7C5CBF
                );
                color: #ffffff;
                border: none;
                border-radius: 12px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a7de0, stop:1 #6a4aaf
                );
            }
            QPushButton:pressed {
                background: #3a6dd0;
            }
            QPushButton:disabled {
                background: #222;
                color: #444;
            }
        """)
        self.setGraphicsEffect(_shadow(20, 6, 100))


class TrainingTab(QWidget):
    SCENE_RU = {
        "boat": "Катер",
        "bubble": "Пузырек",
        "bug": "Жук",
        "butterfly": "Бабочка",
        "mouse": "Мышонок",
        "plane": "Самолет",
        "star": "Звезда"
    }

    BL_RU = {
        "Healthy": "Нет нарушений",
        "Deuteranopia": "Дейтеранопия",
        "Protanopia": "Протанопия",
        "Tritanopia": "Тританопия",
        "Achromatopsia": "Ахроматопсия",
    }

    DISEASE_RU = {
        "myopia": "Миопия",
        "hyperopia": "Гиперметропия"
    }

    training_finished = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_ex_index = 0
        self._exercise_plan = {}
        self._current_user_id = None
        self._renderer_process = None
        self._frame_reader_thread = None
        self._process_monitor_thread = None
        self._camera_recorder_thread = None

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._video_frame = QFrame()
        self._video_frame.setVisible(False)
        self._video_frame.setStyleSheet("background: #000000; border: none;")
        self._video_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        video_lay = QVBoxLayout(self._video_frame)
        video_lay.setContentsMargins(0, 0, 0, 0)
        
        self._graphics_view = QGraphicsView()
        self._graphics_view.setStyleSheet("background: #000000; border: none;")
        self._graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._graphics_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._graphics_scene = QGraphicsScene()
        self._graphics_view.setScene(self._graphics_scene)
        self._graphics_pixmap_item = QGraphicsPixmapItem()
        self._graphics_scene.addItem(self._graphics_pixmap_item)
        
        video_lay.addWidget(self._graphics_view)
        
        stop_btn_container = QFrame()
        stop_btn_container.setFixedHeight(60)
        stop_btn_container.setStyleSheet("background: rgba(0, 0, 0, 200); border: none;")
        stop_lay = QHBoxLayout(stop_btn_container)
        stop_lay.setContentsMargins(24, 0, 24, 0)
        stop_lay.addStretch()
        
        self._stop_btn = LaunchButton("Остановить")
        self._stop_btn.setFixedWidth(200)
        self._stop_btn.clicked.connect(self._stop_training)
        stop_lay.addWidget(self._stop_btn)
        video_lay.addWidget(stop_btn_container, alignment=Qt.AlignmentFlag.AlignBottom)
        
        root.addWidget(self._video_frame)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(48, 36, 48, 48)
        lay.setSpacing(0)

        header = QHBoxLayout()
        header.setSpacing(0)

        title_col = QVBoxLayout()
        title_col.setSpacing(6)

        self._title = QLabel("Программа тренировок")
        self._title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self._title.setStyleSheet("color: #ffffff; background: transparent;")
        title_col.addWidget(self._title)

        header.addLayout(title_col, stretch=1)

        self._launch_btn = LaunchButton("Запустить гимнастику")
        self._launch_btn.setFixedWidth(240)
        self._launch_btn.clicked.connect(self._launch_gymnastics)
        header.addWidget(self._launch_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        lay.addLayout(header)
        lay.addSpacing(32)

        self._params_frame = QFrame()
        self._params_frame.setVisible(False)
        params_lay = QVBoxLayout(self._params_frame)
        params_lay.setContentsMargins(0, 0, 0, 0)
        params_lay.setSpacing(16)

        section_lbl = QLabel("ПАРАМЕТРЫ ПЛАНА")
        section_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        section_lbl.setStyleSheet("color: #888; letter-spacing: 2px; background: transparent;")
        params_lay.addWidget(section_lbl)

        self._params_grid = QGridLayout()
        self._params_grid.setSpacing(12)
        params_lay.addLayout(self._params_grid)

        lay.addWidget(self._params_frame)
        lay.addSpacing(32)

        self._exercises_frame = QFrame()
        self._exercises_frame.setVisible(False)
        ex_lay = QVBoxLayout(self._exercises_frame)
        ex_lay.setContentsMargins(0, 0, 0, 0)
        ex_lay.setSpacing(16)

        ex_header = QHBoxLayout()
        ex_section = QLabel("СПИСОК УПРАЖНЕНИЙ")
        ex_section.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        ex_section.setStyleSheet("color: #888; letter-spacing: 2px; background: transparent;")
        ex_header.addWidget(ex_section)
        ex_header.addStretch()

        self._ex_count = QLabel("")
        self._ex_count.setFont(QFont("Segoe UI", 9))
        self._ex_count.setStyleSheet("color: #444; background: transparent;")
        ex_header.addWidget(self._ex_count)
        ex_lay.addLayout(ex_header)

        self._exercises_lay = QVBoxLayout()
        self._exercises_lay.setSpacing(8)
        ex_lay.addLayout(self._exercises_lay)

        lay.addWidget(self._exercises_frame)
        lay.addSpacing(32)

        scroll.setWidget(container)
        root.addWidget(scroll)

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

        self._clear_grid()

        params = [
            ("Диагноз", f"{disease_ru} {level}", "#5B8DEF"),
            ("Сцена", scene_ru, "#7C5CBF"),
            ("Цветовое зрение", bl_ru, "#48CAE4"),
        ]

        for i, (label, value, accent) in enumerate(params):
            card = ParamCard(label, value, accent)
            self._params_grid.addWidget(card, 0, i)

        self._params_frame.setVisible(True)

        self._clear_exercises()
        exercises = plan.get("exercises", [])
        self._ex_count.setText(f"{len(exercises)} упражнений")
        for i, ex in enumerate(exercises, 1):
            card = ExerciseCard(ex, i)
            self._exercises_lay.addWidget(card)
        self._exercises_frame.setVisible(bool(exercises))

    def _clear_grid(self):
        while self._params_grid.count():
            item = self._params_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _clear_exercises(self):
        while self._exercises_lay.count():
            item = self._exercises_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _get_plan(self) -> dict:
        return self._exercise_plan or {
            "scene": "star",
            "object_scale": 1.0,
            "speed_ms": 2,
            "bl_type": "Healthy",
        }

    # def _analyze_results(self, gaze_data):
    #     PROJECT_ROOT = Path(__file__).resolve()
    #     while not (PROJECT_ROOT / "python_renderer").exists() and PROJECT_ROOT.parent != PROJECT_ROOT:
    #         PROJECT_ROOT = PROJECT_ROOT.parent
    #     log_path = PROJECT_ROOT / "data" / "gymnastics.log"
    #     try:
    #         target_data = []
    #         if log_path.exists():
    #             with open(log_path, "r", encoding="utf-8") as f:
    #                 for line in f:
    #                     try:
    #                         d = json.loads(line)
    #                         if d.get("levelname") == "INFO":
    #                             target_data.append({'duration': d['duration'], 'x_coord': d['x_coord'], 'y_coord': d['y_coord']})
    #                     except Exception: continue
    #         if not target_data or not gaze_data: return
    #         GROUND_SIZE, W, H = 12.0 * 0.85, 1280, 720
    #         for p in target_data:
    #             p['x_coord'] = int((p['x_coord'] / GROUND_SIZE + 1.0) * 0.5 * W)
    #             p['y_coord'] = int((p['y_coord'] / GROUND_SIZE + 1.0) * 0.5 * H)
    #         validator = ExerciseValidator(threshold=175.0, window_size=10)
    #         report = validator.validate(target_data, gaze_data)
    #         self.training_finished.emit(report)
    #     except Exception as e:
    #            print(f"[TrainingTab] analysis error: {e}")
    #            self.training_finished.emit(default_report)

    def _stop_training(self):
        print("[TrainingTab] Stopping training")
        self._current_ex_index = 0
        
        # Stop camera recording
        if self._camera_recorder_thread:
            print("[TrainingTab] Stopping camera recorder...")
            self._camera_recorder_thread.stop()
            self._camera_recorder_thread = None
        
        if self._frame_reader_thread:
            self._frame_reader_thread.stop()
            self._frame_reader_thread = None
        
        if self._process_monitor_thread:
            self._process_monitor_thread.stop()
            self._process_monitor_thread = None
        
        if self._renderer_process:
            try:
                self._renderer_process.terminate()
                self._renderer_process.wait(timeout=2)
                if self._renderer_process.poll() is None:
                    self._renderer_process.kill()
            except Exception as e:
                print(f"[TrainingTab] Error terminating process: {e}")
            finally:
                self._renderer_process = None
        
        if hasattr(self, '_graphics_pixmap_item'):
            self._graphics_pixmap_item.setPixmap(QPixmap())
        
        self._video_frame.setVisible(False)
        
        print("[TrainingTab] Training stopped")

    def _launch_gymnastics(self):
        if self._renderer_process or self._frame_reader_thread or self._process_monitor_thread:
            print("[TrainingTab] Cleaning up existing training session...")
            self._stop_training()
            time.sleep(1.0)
        
        exercises = self._exercise_plan.get("exercises", [])
        if not exercises:
            print("[TrainingTab] No exercises in plan")
            return
            
        exercise = exercises[0]
        exercise_name = exercise.get("name", "circle_right")
        bl_type = self._exercise_plan.get("bl_type", "Healthy")
        scene = self._exercise_plan.get("scene", "star")
        speed_raw = self._exercise_plan.get("speed_ms", 2)
        
        try:
            speed_ms = int(float(speed_raw))
        except (ValueError, TypeError):
            speed_ms = 2
        
        width, height = 1280, 720

        renderer_dir = Path(__file__).resolve().parent.parent / "python_renderer"
        if not renderer_dir.exists():
            renderer_dir = Path(__file__).resolve().parent.parent.parent / "python_renderer"
        
        if sys.platform == "win32":
            python_exe = renderer_dir / ".venv" / "Scripts" / "python.exe"
            venv_path = renderer_dir / ".venv" / "Scripts"
        else:
            python_exe = renderer_dir / ".venv" / "bin" / "python3"
            venv_path = renderer_dir / ".venv" / "bin"
        
        renderer_script = renderer_dir / "renderer.py"
        
        if not python_exe.exists() or not renderer_script.exists():
            print(f"[TrainingTab] Error: Cannot find renderer at {renderer_dir}")
            return

        args = [
            str(python_exe),
            str(renderer_script),
            "1",
            bl_type,
            exercise_name,
            scene,
            str(speed_ms),
            str(width),
            str(height),
        ]

        print("[TrainingTab] Launching renderer", args)
        
        env = os.environ.copy()
        if venv_path.exists():
            env["VIRTUAL_ENV"] = str(renderer_dir / ".venv")
            env["PATH"] = f"{str(venv_path)}:{env.get('PATH', '')}"
        env["PYTHONPATH"] = str(renderer_dir.parent)

        if hasattr(self, '_graphics_pixmap_item'):
            self._graphics_pixmap_item.setPixmap(QPixmap())

        self._renderer_process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(renderer_dir),
            env=env
        )
        
        self._video_frame.setVisible(True)
        self._video_frame.raise_()
        
        self._process_monitor_thread = ProcessMonitorThread(self._renderer_process)
        self._process_monitor_thread.finished_naturally.connect(self._on_renderer_finished)
        self._process_monitor_thread.start()
        
        time.sleep(0.5)
        
        self._frame_reader_thread = FrameReaderThread()
        self._frame_reader_thread.frameReady.connect(
            self._update_frame, 
            Qt.ConnectionType.QueuedConnection
        )
        self._frame_reader_thread.start()
        
        self._camera_recorder_thread = CameraRecorderThread()
        self._camera_recorder_thread.recording_started.connect(self._on_camera_recording_started)
        self._camera_recorder_thread.recording_error.connect(self._on_camera_recording_error)
        self._camera_recorder_thread.start()
        print("[TrainingTab] Camera recording started")

    def _on_renderer_finished(self):
        print("[TrainingTab] Plan finished")
        self._stop_training()

    def _on_camera_recording_started(self):
        print("[TrainingTab] Camera recording has started successfully")

    def _on_camera_recording_error(self, error_msg: str):
        print(f"[TrainingTab] Camera recording error: {error_msg}")

    def _update_frame(self, pixmap: QPixmap):
        if pixmap.isNull():
            return

        if self._current_ex_index == 0 and not hasattr(self, "_first_frame_received"):
            self._first_frame_received = True
            print("[TrainingTab] First frame received!")

        self._graphics_pixmap_item.setPixmap(pixmap)
        QTimer.singleShot(10, self._fit_view_to_pixmap)

    def _fit_view_to_pixmap(self):
        """Fit the graphics view to the current pixmap"""
        if hasattr(self, '_graphics_pixmap_item') and self._graphics_pixmap_item:
            pixmap = self._graphics_pixmap_item.pixmap()
            if pixmap and not pixmap.isNull():
                self._graphics_view.fitInView(
                    self._graphics_pixmap_item,
                    Qt.AspectRatioMode.KeepAspectRatio
                )

    def _stop_training(self):
        print("[TrainingTab] Stopping training")
        self._current_ex_index = 0
        
        if hasattr(self, "_first_frame_received"):
            delattr(self, "_first_frame_received")
        
        if self._frame_reader_thread:
            print("[TrainingTab] Stopping frame reader...")
            self._frame_reader_thread.stop()
            self._frame_reader_thread = None
        
        if self._process_monitor_thread:
            print("[TrainingTab] Stopping process monitor...")
            try:
                self._process_monitor_thread.finished_naturally.disconnect()
            except:
                pass
            self._process_monitor_thread.stop()
            self._process_monitor_thread = None
        
        if self._renderer_process:
            try:
                self._renderer_process.terminate()
                self._renderer_process.wait(timeout=2)
                if self._renderer_process.poll() is None:
                    self._renderer_process.kill()
                    self._renderer_process.wait()
            except Exception as e:
                print(f"[TrainingTab] Error terminating process: {e}")
                try:
                    self._renderer_process.kill()
                except:
                    pass
            finally:
                self._renderer_process = None
        
        if hasattr(self, '_graphics_pixmap_item'):
            self._graphics_pixmap_item.setPixmap(QPixmap())
        
        self._video_frame.setVisible(False)
        
        if hasattr(self, '_launch_btn'):
            self._launch_btn.setEnabled(True)
        
        print("[TrainingTab] Training stopped")

    def _cleanup(self):
        print("[TrainingTab] Cleaning up resources...")
        try:
            if self._process_monitor_thread:
                try:
                    self._process_monitor_thread.finished_naturally.disconnect()
                except:
                    pass
            
            if self._frame_reader_thread:
                self._frame_reader_thread.stop()
                self._frame_reader_thread = None
            
            if self._process_monitor_thread:
                self._process_monitor_thread.stop()
                self._process_monitor_thread = None
            
            if self._renderer_process:
                try:
                    self._renderer_process.terminate()
                    self._renderer_process.wait(timeout=1)
                    if self._renderer_process.poll() is None:
                        self._renderer_process.kill()
                except:
                    pass
                self._renderer_process = None
            
            if sys.platform != "win32":
                shm_path = "/dev/shm/frames"
                if os.path.exists(shm_path):
                    try:
                        os.remove(shm_path)
                    except:
                        pass
        except Exception as e:
            print(f"[TrainingTab] Error during cleanup: {e}")
        print("[TrainingTab] Cleanup complete")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._video_frame.isVisible() and hasattr(self, '_graphics_pixmap_item'):
            QTimer.singleShot(50, self._fit_view_to_pixmap)

    def closeEvent(self, event):
        self._cleanup()
        super().closeEvent(event)