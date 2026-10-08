import os
from core.config import IMG_DIR, SIZE, PIL_AVAILABLE
from core.xml_parser import ALL_REQUIRED_FRAMES

if PIL_AVAILABLE:
    from PIL import Image, ImageTk
    import numpy as np

class SpriteManager:
    def __init__(self):
        self.images = {}
        self.tk_images = {}
        self.load_images()

    def load_images(self):
        if not PIL_AVAILABLE:
            return
        all_names = set(ALL_REQUIRED_FRAMES)
        if os.path.exists(IMG_DIR):
            for fname in os.listdir(IMG_DIR):
                if fname.lower().endswith(".png"):
                    all_names.add(os.path.splitext(fname)[0])
        for name in all_names:
            path = os.path.join(IMG_DIR, name + ".png")
            if os.path.exists(path):
                try:
                    raw_img = Image.open(path).convert("RGBA").resize((SIZE, SIZE))
                    # Perfectly binarize alpha and clear transparent pixels to eliminate dark fringe artifacts
                    arr = np.array(raw_img)
                    transparent_mask = arr[:, :, 3] < 120
                    arr[transparent_mask] = [0, 0, 1, 0]
                    arr[~transparent_mask, 3] = 255
                    self.images[name] = Image.fromarray(arr)
                except Exception:
                    pass

    def get(self, name: str, flipped: bool = False, rotation: int = 0):
        return self.get_tk_image(name, rotation=rotation, flip_h=flipped)

    def get_tk_image(self, name: str, rotation: int = 0, flip_h: bool = False, flip_v: bool = False):
        if not PIL_AVAILABLE:
            return None
        key = f"{name}_r{rotation}_fh{flip_h}_fv{flip_v}"
        if key not in self.tk_images:
            img = self.images.get(name)
            if img is None:
                if self.images:
                    img = next(iter(self.images.values()))
                else:
                    return None
            if flip_h:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            if flip_v:
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
            if rotation:
                img = img.rotate(rotation, expand=False)
            self.tk_images[key] = ImageTk.PhotoImage(img)
        return self.tk_images[key]
