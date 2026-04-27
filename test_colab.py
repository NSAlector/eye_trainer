import time

from PIL import Image

import requests
import numpy as np
from colab_api import ColabAPI
from color_code import ade_palet 
transform = ColabAPI("https://send-krypton-straining.ngrok-free.dev")

def create_test_mask():
    mask = np.zeros((512, 512, 3), dtype=np.uint8)
    sky_color = ade_palet[3]
    mask[0:256, :] = sky_color
    grass_color = ade_palet[1]
    mask[256:512, :] = grass_color
    
    Image.fromarray(mask).save("test_mask.png")
    print(f"Sky color (class 3): {sky_color}")
    print(f"Grass color (class 10): {grass_color}")
    return mask
def main():
    start_time = time.perf_counter()
    
    create_test_mask()
    if transform.health_check():
        print("connected to Colab API")
        
        with open("test_mask.png", "rb") as f:
            mask_bytes = f.read()
        
        result = transform.process_frame(mask_bytes)
        
        Image.fromarray(result).save("generated_output.png")
        print("saved generated_output.png")
        end_time = time.perf_counter()
        print(f"Processing time: {end_time - start_time:.2f} seconds")
    else:
        print("cannot reach Colab API")


if __name__ == "__main__":
    main()
