# hypergan_transform.py
import sys
import numpy as np
import torch
from pathlib import Path
from PIL import Image
import torchvision.transforms as T

class HyPERGANTransform:
    def __init__(
        self,
        repo_path: str,
        checkpoint_path: str,
        input_size: int | None = 512,
    ):
        repo_path = str(Path(repo_path).resolve())
        if repo_path not in sys.path:
            sys.path.insert(0, repo_path)

        from main import UNetGenerator
        self.GeneratorClass = UNetGenerator
        
        self.device = torch.device("cpu")
        self.input_size = input_size

        self.net = self.GeneratorClass().to(self.device)
        
        state = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        
        if "generator" in state:
            state = state["generator"]
        elif "state_dict" in state:
            state = state["state_dict"]
        elif "model" in state:
            state = state["model"]
        
        self.net.load_state_dict(state)
        self.net.eval()
        t = []
        if input_size:
            t.append(T.Resize((input_size, input_size), T.InterpolationMode.BICUBIC))
        t += [
            T.ToTensor(),
            T.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ]
        self.preprocess = T.Compose(t)

    @torch.no_grad()
    def transform(self, frame: np.ndarray) -> np.ndarray:
        orig_h, orig_w = frame.shape[:2]
        pil = Image.fromarray(frame)
        tensor = self.preprocess(pil).unsqueeze(0).to(self.device)

        out = self.net(tensor)
        out = (out * 0.5 + 0.5).clamp(0, 1)
        out_np = (out.squeeze(0).permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)

        if self.input_size and (orig_h != self.input_size or orig_w != self.input_size):
            out_np = np.array(
                Image.fromarray(out_np).resize((orig_w, orig_h), Image.BICUBIC)
            )
        return out_np

    def reset(self):
        pass