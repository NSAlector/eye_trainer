import numpy as np
import io
import base64
from PIL import Image
import time
import requests
from color_code import ade_palet
#transforms frame and gives numpy frame out
#connect with api_url


def get_classes(rgb_image, palette=ade_palet):
    h, w = rgb_image.shape[:2]
    class_id_map = np.zeros((h, w), dtype=np.uint8)
    for class_id, rgb_color in enumerate(palette):
        #get all pixels that match this specific RGB color
        mask = np.all(rgb_image == rgb_color, axis=-1)
        class_id_map[mask] = class_id
    return class_id_map

class ColabAPI:
    def __init__(self, api_url):
        self.api_url = api_url.rstrip('/')
        self.max_retries = 3
        self.retry_delay = 2
        # header to bypass ngrok warning page
        self.headers = {
            "ngrok-skip-browser-warning": "true",
            "Content-Type": "application/json"
        }
    
    #processing only accepts bytes or file-like objects
    def process_frame(self, frame):
        if isinstance(frame, bytes):
            mask_pil_rgb = Image.open(io.BytesIO(frame)).convert("RGB")
        elif hasattr(frame, 'read'):
            mask_pil_rgb = Image.open(frame).convert("RGB")
        
        mask_np_rgb = np.array(mask_pil_rgb)
        mask_resized = np.array(Image.fromarray(mask_np_rgb).resize((256, 256), Image.NEAREST))
        class_id_map_np = get_classes(mask_resized, ade_palet)

        class_id_pil = Image.fromarray(class_id_map_np.astype(np.uint8), mode='L')
        buf = io.BytesIO()
        class_id_pil.save(buf, format='PNG')
        img_b64 = base64.b64encode(buf.getvalue()).decode()

        retries = self.max_retries
        for attempt in range(retries):
            try:
                resp = requests.post(
                    self.api_url,
                    json={"mask": img_b64},
                    headers=self.headers, 
                    timeout=120
                )
                
                print(f"Response status: {resp.status_code}")
                resp.raise_for_status()
                
                result = resp.json()
                if 'error' in result:
                    raise Exception(f"API error: {result['error']}")
                
                img_data = base64.b64decode(result['image'])
                result_img = Image.open(io.BytesIO(img_data))
                return np.array(result_img)
                
            except requests.exceptions.ConnectionError as e:
                if attempt < retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Colab API not reachable. URL: {self.api_url}")
                    
            except requests.exceptions.Timeout:
                print(f"timeout (attempt {attempt + 1}/{retries})")
                if attempt < retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise Exception("Request timed out")
    def health_check(self):
        try:
            resp = requests.get(f"{self.api_url}/health", headers=self.headers, timeout=5)
            return resp.status_code == 200
        except:
            return False
