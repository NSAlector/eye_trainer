import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.render.render import EyeGymnasticsOne
from enumData.bltype import blType
from src.render.scenes import scenes
from src.render.movements import movements
from pathlib import Path


sys.stdout.reconfigure(line_buffering=True)
def launch_scene(argv):
    user_vision = blType[argv[2]]
    selected_movement = movements[argv[3]]
    selected_scene = scenes[argv[4]]
    selected_speed = int(argv[5])
    width = int(argv[6])
    height = int(argv[7])

    if argv[1] == "1":
        scene = EyeGymnasticsOne(bl_type=user_vision, movement_func=selected_movement, scene_type = selected_scene,
                               speed = selected_speed, width=width, height=height)
    # else:
    #     app = EyeGymnasticsTwo(bl_type=user_vision, movement_func=selected_movement,
    #                            width=width, height=height)
    try:
        print(f"Starting session for {user_vision.name}...")
        scene.run()
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    launch_scene(sys.argv)