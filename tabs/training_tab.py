import mmap 
import os
from datetime import datetime, time
import sys
import json
import time
import random

import numpy as np

import struct
import subprocess
from pathlib import Path
import threading

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QGridLayout,
    QGraphicsDropShadowEffect, QSizePolicy, QGraphicsScene,
    QGraphicsPixmapItem, QGraphicsView
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Signal, QProcess, QThread, QTimer
from PySide6.QtGui import QFont, QColor, QLinearGradient, QPainter, QPen, QPixmap, QImage
from utils.sharedMemoryFileWriter import SharedMemoryWriter
from utils.sharedMemoryFileReader import SharedMemoryReader
from tabs.validation import ExerciseValidator



class ProcessMonitorThread(QThread):
    def __init__(self, process):
        super().__init__()
        self.process = process
        self._running = True

    def _read_stream(self, stream, prefix):
        while self._running:
            try:
                line = stream.readline()
                if not line:
                    break
                if isinstance(line, bytes):
                    line = line.decode('utf-8', errors='ignore')
                if line.strip():
                    print(f"{prefix} {line.rstrip()}")
            except Exception as e:
                break

    def run(self):
        threads = []
        
        if self.process.stdout:
            t_out = threading.Thread(
                target=self._read_stream,
                args=(self.process.stdout, "[Renderer]"),
                daemon=True
            )
            t_out.start()
            threads.append(t_out)

        if self.process.stderr:
            t_err = threading.Thread(
                target=self._read_stream,
                args=(self.process.stderr, "[Renderer STDERR]"),
                daemon=True
            )
            t_err.start()
            threads.append(t_err)

        self.process.wait()
        self._running = False
        
        for t in threads:
            t.join(timeout=1)

        print(f"[ProcessMonitorThread] Exit code: {self.process.poll()}")

    def stop(self):
        self._running = False
        self.wait(2000)


class FrameReaderThread(QThread):
    frameReady = Signal(QPixmap)

    def __init__(self, cyclegan_transform=None):

        super().__init__()
        self.reader = SharedMemoryReader("frames")
        self.running = False
        self._cyclegan = ColabLTXTransform(
            api_url="https://your-ngrok-url.ngrok-free.app",
            prompt="photorealistic nature scene, smooth motion, vivid colors",
            strength=0.65,  # lower = closer to original motion, higher = more stylized
    )
    def run(self):
        self.running = True
        while self.running:
            frame = self.reader.read_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            try:
                if self._cyclegan is not None:
                    frame = self._cyclegan.transform(frame)

                h, w = frame.shape[:2]
                if not frame.flags['C_CONTIGUOUS']:
                    frame = np.ascontiguousarray(frame)

                qt_image = QImage(frame.data, w, h, 3 * w, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image.copy())
                if not pixmap.isNull():
                    self.frameReady.emit(pixmap)

            except Exception as e:
                print(f"[FrameReaderThread] Error: {e}")

            except Exception as e:
                print(f"[FrameReaderThread] Error: {e}")

        self.reader.close()

    def stop(self):
        self.running = False
        self.wait(2000)




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
        "very_slow":("Очень медленно", "#7C5CBF"),
        "slow":("Медленно", "#5B8DEF"),
        "medium":("Стандартно", "#3DB87A"),
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

        speed = exercise.get("speed_ms", "medium")
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

    BACKGROUND_RU = {
        "floor.png": "Паркет",
        "grass.png": "Трава",
        "night_sky.png": "Ночное небо",
        "sky.png": "Небо",
        "underwater.png": "Подводный мир",
        "water.png": "Спокойное море",
    }

    training_finished = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._exercise_plan = {}
        self._current_user_id = None
        self._renderer_process = None
        self._frame_reader_thread = None
        self._process_monitor_thread = None
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
        
        if "speed_ms" in self._exercise_plan:
            try:
                speed_raw = self._exercise_plan["speed_ms"]
                if isinstance(speed_raw, (int, float)):
                    self._exercise_plan["speed_ms"] = int(speed_raw)
                else:
                    self._exercise_plan["speed_ms"] = int(float(str(speed_raw)))
            except (ValueError, TypeError):
                self._exercise_plan["speed_ms"] = 30

        disease = plan.get("disease", "")
        level = plan.get("level", "")
        scene_id = plan.get("scene", "star")
        bl_type = plan.get("bl_type", "Healthy")

        disease_ru = self.DISEASE_RU.get(disease, disease.capitalize())
        scene_ru = self.SCENE_RU.get(scene_id, scene_id)
        bl_ru = self.BL_RU.get(bl_type, "Норма")

        self._clear_grid()

        speed_display = self._exercise_plan.get("speed_ms", 30)
        params = [
            ("Диагноз", f"{disease_ru} {level}", "#5B8DEF"),
            ("Сцена", scene_ru, "#7C5CBF"),
            ("Цветовое зрение", bl_ru, "#48CAE4"),
            ("Скорость", f"{speed_display} мс", "#F4A261"),
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

    def load_plan_from_db(self, user_id: int):
        try:
            from utils.db_manager import DatabaseManager
            from repositories.exercise_repository import ExerciseRepository
            db = DatabaseManager()
            repo = ExerciseRepository(db)
            plan = repo.get_plan(user_id)
            db.close()
            if plan:
                self.apply_plan(plan, user_id)
        except Exception as e:
            print(f"[TrainingTab] план из БД недоступен: {e}")

    def _get_plan(self) -> dict:
        return self._exercise_plan or {
            "scene": "star",
            "object_scale": 1.0,
            "speed_ms": 30,
            "bl_type": "Healthy",
        }

    def _launch_gymnastics(self):
        if self._renderer_process or self._frame_reader_thread or self._process_monitor_thread:
            print("[TrainingTab] Cleaning up existing training session...")
            self._stop_training()
            time.sleep(1.0)
        
        if sys.platform != "win32":
            shm_path = "/dev/shm/frames"
            if os.path.exists(shm_path):
                try:
                    os.remove(shm_path)
                    print(f"[TrainingTab] Removed existing shared memory: {shm_path}")
                except Exception as e:
                    print(f"[TrainingTab] Could not remove shared memory: {e}")

        exercises = self._exercise_plan.get("exercises", [])
        if not exercises:
            print("[TrainingTab] No exercises in plan")
            return
            
        exercise = exercises[0]
        exercise_name = exercise.get("name", "circle_right")
        bl_type = self._exercise_plan.get("bl_type", "Healthy")
        scene = self._exercise_plan.get("scene", "star")
        speed_raw = self._exercise_plan.get("speed_ms", 30)
        
        try:
            if isinstance(speed_raw, (int, float)):
                speed_ms = int(speed_raw)  
            else:
                speed_ms = int(float(str(speed_raw))) 
        except (ValueError, TypeError):
            speed_ms = 2 
        
        print(f"[TrainingTab] Speed raw: {speed_raw} ({type(speed_raw)}) -> converted: {speed_ms}")
        
        width, height = 1280, 720

        renderer_dir = Path(__file__).resolve().parent.parent / "python_renderer"
        
        if sys.platform == "win32":
            python_exe = renderer_dir / ".venv" / "Scripts" / "python.exe"
            clean_script = renderer_dir.parent / "clean.bat"
            venv_path = renderer_dir / ".venv" / "Scripts"
        else:
            python_exe = renderer_dir / ".venv" / "bin" / "python3"
            clean_script = renderer_dir.parent / "clean.sh"
            venv_path = renderer_dir / ".venv" / "bin"
        
        renderer_script = renderer_dir / "renderer.py"
        
        if clean_script.exists() and not hasattr(self, '_cleaned'):
            try:
                if sys.platform == "win32":
                    p = subprocess.Popen([str(clean_script)], shell=True)
                else:
                    p = subprocess.Popen([str(clean_script)])
                p.wait(timeout=5)
                print(f"[TrainingTab] Cleaned environment")
                self._cleaned = True
            except Exception as e:
                print(f"[TrainingTab] Warning: Clean script failed: {e}")

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
        self._process_monitor_thread.start()
        
        time.sleep(0.5)
        self._frame_reader_thread = FrameReaderThread()
        self._frame_reader_thread.frameReady.connect(
            self._update_frame, 
            Qt.ConnectionType.QueuedConnection
        )
        self._frame_reader_thread.start()

    def _stop_training(self):
        print("[TrainingTab] Stopping training")
        
        if self._frame_reader_thread:
            print("[TrainingTab] Stopping frame reader...")
            self._frame_reader_thread.stop()
            self._frame_reader_thread = None
        
        if self._process_monitor_thread:
            print("[TrainingTab] Stopping process monitor...")
            self._process_monitor_thread.stop()
            self._process_monitor_thread = None
        
        if self._renderer_process:
            print("[TrainingTab] Terminating renderer process...")
            try:
                self._renderer_process.terminate()
                self._renderer_process.wait(timeout=3)
                if self._renderer_process.poll() is None:
                    print("[TrainingTab] Force killing renderer...")
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
        
        print("[TrainingTab] Training stopped")

    def _cleanup(self):
        print("[TrainingTab] Cleaning up resources...")
        try:
            self._stop_training()
            if sys.platform != "win32":
                shm_path = "/dev/shm/frames"
                if os.path.exists(shm_path):
                    try:
                        os.remove(shm_path)
                        print(f"[TrainingTab] Removed shared memory: {shm_path}")
                    except:
                        pass
        except Exception as e:
            print(f"[TrainingTab] Error during cleanup: {e}")
        print("[TrainingTab] Cleanup complete")

    def _update_frame(self, pixmap: QPixmap):
        if pixmap.isNull():
            return
        
        self._graphics_pixmap_item.setPixmap(pixmap)
        QTimer.singleShot(10, self._fit_view_to_pixmap)

    def _fit_view_to_pixmap(self):
        if hasattr(self, '_graphics_pixmap_item') and self._graphics_pixmap_item:
            pixmap = self._graphics_pixmap_item.pixmap()
            if pixmap and not pixmap.isNull():
                self._graphics_view.fitInView(
                    self._graphics_pixmap_item,
                    Qt.AspectRatioMode.KeepAspectRatio
                )

    def _stop_training(self):
        print("[TrainingTab] Stopping training")
        
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
        
        renderer_dir = Path(__file__).resolve().parent.parent / "python_renderer"
        
        if sys.platform == "win32":
            clean_script = renderer_dir.parent / "clean.bat"
        else:
            clean_script = renderer_dir.parent / "clean.sh"
        
        
        if clean_script.exists():
            try:
                if sys.platform == "win32":
                    p = subprocess.Popen([str(clean_script)], shell=True)
                else:
                    p = subprocess.Popen([str(clean_script)])
                p.wait(timeout=5)
                print(f"[TrainingTab] Cleaned environment")
            except Exception as e:
                print(f"[TrainingTab] Warning: Clean script failed: {e}")


        if hasattr(self, '_graphics_pixmap_item'):
            self._graphics_pixmap_item.setPixmap(QPixmap())
        
        self._video_frame.setVisible(False)
        
        print("[TrainingTab] Training stopped")

    def _cleanup(self):
        print("[TrainingTab] Cleaning up resources...")
        try:
            self._stop_training()
        except Exception as e:
            print(f"[TrainingTab] Error during cleanup: {e}")
        print("[TrainingTab] Cleanup complete")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._video_frame.isVisible() and hasattr(self, '_graphics_pixmap_item'):
            QTimer.singleShot(50, self._fit_view_to_pixmap)
    
    def _generate_fake_gaze(self, target_data):
        gaze = []
        for p in target_data:
            noise_x = random.uniform(-1.5, 1.5)
            noise_y = random.uniform(-1.5, 1.5)

            anomaly = 0
            if 3.0 < p['duration'] < 4.5:
                anomaly = 15

            gaze.append({
                'duration': p['duration'],
                'x_coord': p['x_coord'] + noise_x + anomaly,
                'y_coord': p['y_coord'] + noise_y + anomaly
            })
        return gaze

    def _analyze_results(self):
            log_path = Path("eye_gymnastics/python_renderer/gymnastics.log")

            if not log_path.exists():
                print("Файл лога не найден")
                return

            try:
                sessions = {}
                with open(log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            sid = data.get("session_id")
                            if sid not in sessions:
                                sessions[sid] = []
                            sessions[sid].append(data)
                        except: continue

                if not sessions: return

                last_sid = list(sessions.keys())[-1]
                last_session_data = sessions[last_sid]

                target_data = []
                for entry in last_session_data:
                    if entry.get("levelname") == "INFO" and entry.get("duration") > 0:
                        target_data.append({
                            'duration': entry['duration'],
                            'x_coord': entry['x_coord'],
                            'y_coord': entry['y_coord']
                        })

                if len(target_data) < 10:
                    print("Слишком мало данных для анализа")
                    return

                gaze_data = self._generate_mock_gaze(target_data)
                validator = ExerciseValidator(threshold=3.0)
                report = validator.validate(target_data, gaze_data)

                self.training_finished.emit(report)

            except Exception as e:
                print(f"Ошибка парсинга лога: {e}")


    def closeEvent(self, event):
        self._cleanup()
        super().closeEvent(event)
        super().closeEvent(event)
