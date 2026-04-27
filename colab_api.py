# colab_ltx_transform.py

import requests
import base64
import numpy as np
import threading
from io import BytesIO
from PIL import Image
from collections import deque


class ColabLTXTransform:
    """
    Sends frame chunks to LTX-Video v2v on Colab, displays stylized frames locally.

    The renderer runs at full speed. Every CHUNK_SIZE frames we fire an async
    request to Colab. While waiting, we display the previous stylized chunk.
    When the new chunk arrives it seamlessly replaces the buffer.
    """

    CHUNK_SIZE = 25 

    def __init__(
        self,
        api_url: str,
        prompt: str = "photorealistic nature scene, vivid colors",
        strength: float = 0.7,
        timeout: int = 60,
    ):
        self.url = api_url.rstrip("/") + "/generate"
        self.prompt = prompt
        self.strength = strength
        self.timeout = timeout

        self._lock = threading.Lock()
        self._stylized_buffer: deque[np.ndarray] = deque()  # stylized frames ready to show
        self._pending_chunk: list[np.ndarray] = []          # raw frames accumulating
        self._request_in_flight = False
        self._headers = {"ngrok-skip-browser-warning": "true"}

    def transform(self, frame: np.ndarray) -> np.ndarray:
        """
        Called per frame from FrameReaderThread.
        Accumulates frames, fires async requests, returns stylized frames when ready.
        Falls back to raw frame if no stylized frames available yet.
        """
        # Accumulate raw frames
        self._pending_chunk.append(frame.copy())

        # When chunk is full and no request in flight, fire request
        if len(self._pending_chunk) >= self.CHUNK_SIZE and not self._request_in_flight:
            chunk = self._pending_chunk[:self.CHUNK_SIZE]
            self._pending_chunk = self._pending_chunk[self.CHUNK_SIZE:]
            self._request_in_flight = True
            threading.Thread(
                target=self._call_api, args=(chunk,), daemon=True
            ).start()

        # Return next stylized frame if available, else raw
        with self._lock:
            if self._stylized_buffer:
                return self._stylized_buffer.popleft()

        return frame  

    def _call_api(self, chunk: list[np.ndarray]):
        try:
            payload = {
                "frames": [self._encode(f) for f in chunk],
                "prompt": self.prompt,
                "strength": self.strength,
            }
            resp = requests.post(
                self.url, json=payload,
                timeout=self.timeout,
                headers=self._headers,
            )
            resp.raise_for_status()
            frames_b64 = resp.json()["frames"]
            stylized = [self._decode(b) for b in frames_b64]

            with self._lock:
                self._stylized_buffer.extend(stylized)

        except Exception as e:
            print(f"[ColabLTXTransform] Request failed: {e}")
        finally:
            self._request_in_flight = False

    def reset(self):
        with self._lock:
            self._stylized_buffer.clear()
        self._pending_chunk.clear()
        self._request_in_flight = False

    @staticmethod
    def _encode(arr: np.ndarray) -> str:
        buf = BytesIO()
        Image.fromarray(arr).save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    @staticmethod
    def _decode(b64: str) -> np.ndarray:
        return np.array(Image.open(BytesIO(base64.b64decode(b64))).convert("RGB"))