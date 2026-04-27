from PIL import Image
import numpy as np
import sys
import mmap
import os
import struct
from utils.sharedMemoryFileWriter import SharedMemoryWriter



class SharedMemoryReader:
    def __init__(self, name="frames"):
        self.name = name
        self.map_file = None
        self.fd = None
        self.last_frame_id = -1
        self.HEADER_SIZE = SharedMemoryWriter.HEADER_SIZE
        self.HEADER_FORMAT = SharedMemoryWriter.HEADER_FORMAT
        self.total_size = 0
        
        if sys.platform == "win32":
            self.path = name
        else:
            self.path = f"/dev/shm/{self.name}"

    def _connect(self):
        if self.map_file:
            return True

        try:
            if sys.platform == "win32":
                self.map_file = mmap.mmap(-1, 0, self.name)
                return True
            else:
                if not os.path.exists(self.path):
                    return False
                
                self.fd = os.open(self.path, os.O_RDONLY)
                header = os.read(self.fd, self.HEADER_SIZE)
                if len(header) < self.HEADER_SIZE:
                    os.close(self.fd)
                    self.fd = None
                    return False

                counter, flag, w, h = struct.unpack(self.HEADER_FORMAT, header)

                if w == 0 or h == 0:
                    os.close(self.fd)
                    self.fd = None
                    return False

                frame_size = w * h * 3
                self.total_size = self.HEADER_SIZE + frame_size
                
                self.map_file = mmap.mmap(self.fd, self.total_size, mmap.MAP_SHARED, mmap.PROT_READ)
                self.last_frame_id = counter - 1

                print(f"[SharedMemoryReader] Connected ({w}x{h})")
                return True

        except Exception as e:
            print(f"[SharedMemoryReader] Connect error: {e}")
            if self.fd:
                os.close(self.fd)
                self.fd = None
            return False

    def read_frame(self):
        if not self._connect():
            return None

        try:
            for _ in range(5):
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
                counter2, flag2, _, _ = struct.unpack(self.HEADER_FORMAT, header2)

                if flag2:
                    continue

                if counter != counter2:
                    continue

                if counter == self.last_frame_id:
                    return None

                self.last_frame_id = counter

                frame = np.frombuffer(frame_data, dtype=np.uint8)
                return frame.reshape((h, w, 3))

            return None

        except Exception as e:
            print(f"[SharedMemoryReader] Read error: {e}")
            return None

    def close(self):
        if self.map_file:
            self.map_file.close()
            self.map_file = None
        if self.fd:
            os.close(self.fd)
            self.fd = None

