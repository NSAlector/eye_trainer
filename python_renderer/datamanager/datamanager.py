import time
import datetime
import json
import os
import logging
from pythonjsonlogger import jsonlogger
from pathlib import Path
from enumData.bltype import blType
import ctypes


class DataManager:
    def __init__(self, data_dir: str = "data"):
        base_path = Path(__file__).parent.parent.parent
        self.data_dir = base_path / data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.start_timestamp = None
        self.frame_count = ctypes.c_uint32(0)
        self.coordinates_buffer = []
        self.session_data = {}
        
        self._setup_logger()
        
    def _setup_logger(self):
        self.logger = logging.getLogger("EyeGymnastics")
        self.logger.setLevel(logging.INFO)
        
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        log_file = self.data_dir / "gymnastics.log"
        handler = logging.FileHandler(filename=log_file, encoding='utf-8')
        
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(levelname)s %(session_id)s %(bl_type)s %(movement)s %(duration).2f %(x_coord).3f %(y_coord).3f %(error_msg)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def start_session(self, bl_type: blType, mv: str):
        self.start_timestamp = time.time()
        self.frame_count = 0
        self.coordinates_buffer = []

        session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_file = self.data_dir / f"session_{session_id}.json"

        self.session_data = {
            "session_id": session_id,
            "color_blindness_type": bl_type.name,
            "movement_function": mv,
            "session_start": datetime.datetime.now().isoformat(),
            "completion_status": "started",
            "coordinates": [] 
        }

        return self.session_data.copy()

    def log_coordinates(self, coord):
        if not self.start_timestamp:
            return
        current_time = time.time() - self.start_timestamp
        self.frame_count += 1

        self.session_data["coordinates"].append({
            'frame': self.frame_count,
            'x':    round(coord[0], 3),
            'y':    round(coord[2], 3),
        })

    def end_session(self, session_data: dict):
        duration = time.time() - self.start_timestamp if self.start_timestamp else 0

        self.session_data.update({
            "session_end":      datetime.datetime.now().isoformat(),
            "duration_seconds": round(duration, 2),
            "total_frames":     self.frame_count,
            "completion_status": session_data.get("status", "unknown")
        })

        with open(self.current_file, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, ensure_ascii=False, indent=4)

        self.logger.info("Session ended", extra={
            'session_id': self.session_data['session_id'],
            'bl_type':    self.session_data['color_blindness_type'],
            'movement':   self.session_data['movement_function'],
            'duration':   duration,
            'x_coord': 0, 'y_coord': 0, 'error_msg': ''
        })

        return self.session_data  
    
    def add_error(self, error: Exception):
            error_msg = f"{type(error).__name__}: {str(error)}"
            
            self.logger.error(
                "Error",
                extra={
                    'session_id': self.session_data.get('session_id', 'unknown'),
                    'bl_type': self.session_data.get('color_blindness_type', 'unknown'),
                    'movement': self.session_data.get('movement_function', 'unknown'),
                    'duration': time.time() - self.start_timestamp if self.start_timestamp else 0,
                    'x_coord': 0,
                    'y_coord': 0,
                    'error_msg': error_msg
                },
                exc_info=True
            )
        
        
