import os


def project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

def assert_dir(name):
    return os.path.join(project_root(), "assets", name)

def scene_dir(name):
    return os.path.join(project_root(), "scenes", name)

scenes = {
    "boat": os.path.join(scene_dir("boat.json")),
    "bubble":  os.path.join(scene_dir("bubble.json")),
    "bug": os.path.join(scene_dir("bug.json")),
    "butterfly": os.path.join(scene_dir("butterfly.json")),
    "mouse": os.path.join(scene_dir("mouse.json")),
    "plane": os.path.join(scene_dir("plane.json")),
    "star": os.path.join(scene_dir("star.json")),
}
