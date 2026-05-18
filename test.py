
import torch
import numpy as np
import sys
import os

sys.path.insert(0, '/home/felix/repo/tmp/eye-trainer-working/HyPER-GAN')
from main import UNetGenerator

ckpt_path = '/home/felix/repo/tmp/eye-trainer-working/HyPER-GAN/pretrained_models/gta2cs.pth'

import time
import torch
import numpy as np
from PIL import Image
import sys

device = torch.device('cpu')
model = UNetGenerator().to(device)
state_dict = torch.load(ckpt_path, map_location=device, weights_only=False)
model.load_state_dict(state_dict)
model.eval()

dummy = np.random.randint(0, 255, (256, 512, 3), dtype=np.uint8)

for _ in range(3):
    tensor = torch.from_numpy(dummy).float() / 255.0
    tensor = tensor.permute(2, 0, 1).unsqueeze(0).to(device)
    with torch.no_grad():
        _ = model(tensor)

num_runs = 20
start = time.time()
for _ in range(num_runs):
    tensor = torch.from_numpy(dummy).float() / 255.0
    tensor = tensor.permute(2, 0, 1).unsqueeze(0).to(device)
    with torch.no_grad():
        output = model(tensor)
elapsed = time.time() - start

print(f"Average inference time: {elapsed/num_runs} s")
print(f"FPS: {num_runs/elapsed:.1f}")
