import textwrap
import tkinter as tk
from core.config import SIZE, PIL_AVAILABLE

if PIL_AVAILABLE:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    import numpy as np

def create_bubble_image(text: str, tail_dir: str = "down", tail_rel_x: float = 0.5):
    try:
        font = ImageFont.truetype("segoeui.ttf", 12)
    except Exception:
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except Exception:
            font = ImageFont.load_default()

    raw_lines = text.strip().split("\n")
    lines = []
    for l in raw_lines:
        stripped = l.strip()
        if not stripped:
            lines.append("")
            continue
        wrapped = textwrap.wrap(stripped, width=28)
        lines.extend(wrapped if wrapped else [""])

    line_bboxes = [font.getbbox(l) if l else (0, 0, 0, 14) for l in lines]
    max_w = max(b[2] - b[0] for b in line_bboxes) if line_bboxes else 40
    line_h = 17
    text_h = len(lines) * line_h

    pad_x = 16
    pad_y = 10
    tail_h = 12
    tail_w = 16

    body_w = max(int(max_w + pad_x * 2), 90)
    body_h = int(text_h + pad_y * 2)

    total_w = body_w
    total_h = body_h + tail_h

    im = Image.new("RGBA", (total_w, total_h), (0, 0, 1, 0))
    draw = ImageDraw.Draw(im)

    bg_color     = (254, 250, 240, 255) # Vintage parchment
    border_color = (138, 14, 30, 255)   # Alastor crimson
    text_color   = (24, 6, 10, 255)     # Dark mahogany

    tail_center_x = int(body_w * tail_rel_x)
    tail_center_x = max(18, min(body_w - 18, tail_center_x))
    tail_left  = tail_center_x - tail_w // 2
    tail_right = tail_center_x + tail_w // 2

    radius = 14

    if tail_dir == "down":
        body_box  = [0, 0, body_w - 1, body_h - 1]
        tail_poly = [(tail_left, body_h - 3), (tail_right, body_h - 3), (tail_center_x, total_h - 1)]
        draw.polygon(tail_poly, fill=bg_color)
        draw.rounded_rectangle(body_box, radius=radius, fill=bg_color, outline=border_color, width=2)
        draw.line([(tail_left, body_h - 2), (tail_center_x, total_h - 1)], fill=border_color, width=2)
        draw.line([(tail_right, body_h - 2), (tail_center_x, total_h - 1)], fill=border_color, width=2)
        draw.line([(tail_left + 1, body_h - 2), (tail_right - 1, body_h - 2)], fill=bg_color, width=2)
        text_y = pad_y
    else:
        body_box  = [0, tail_h, body_w - 1, total_h - 1]
        tail_poly = [(tail_left, tail_h + 2), (tail_right, tail_h + 2), (tail_center_x, 0)]
        draw.polygon(tail_poly, fill=bg_color)
        draw.rounded_rectangle(body_box, radius=radius, fill=bg_color, outline=border_color, width=2)
        draw.line([(tail_left, tail_h + 1), (tail_center_x, 0)], fill=border_color, width=2)
        draw.line([(tail_right, tail_h + 1), (tail_center_x, 0)], fill=border_color, width=2)
        draw.line([(tail_left + 1, tail_h + 1), (tail_right - 1, tail_h + 1)], fill=bg_color, width=2)
        text_y = tail_h + pad_y

    for line in lines:
        draw.text((pad_x, text_y), line, font=font, fill=text_color)
        text_y += line_h

    arr = np.array(im)
    arr[arr[:, :, 3] < 128] = [0, 0, 1, 0]
    arr[arr[:, :, 3] >= 128, 3] = 255
    return Image.fromarray(arr)

class SpeechBubbleManager:
    def __init__(self, root):
        self.root = root
        self.bubble_win = None
        self.bubble_after = None
        self._bubble_w = 0
        self._bubble_h = 0
        self._bubble_tail_dir = "down"
        self._tk_img_ref = None

    def show_speech(self, text: str, mascot_x: float, mascot_y: float, sw: int, sh: int):
        if not text:
            return
        self.destroy_bubble()

        tail_dir = "up" if mascot_y < 160 else "down"

        est_w = min(max(len(text) * 8 + 32, 100), 280)
        bx = int(mascot_x) + SIZE // 2 - est_w // 2
        bx = max(10, min(bx, sw - est_w - 10))
        target_tail_x = (int(mascot_x) + SIZE // 2) - bx
        tail_rel_x = max(0.2, min(0.8, target_tail_x / max(1, est_w)))

        im = create_bubble_image(text, tail_dir=tail_dir, tail_rel_x=tail_rel_x)
        bw = im.width
        bh = im.height

        bx = int(mascot_x) + SIZE // 2 - bw // 2
        bx = max(10, min(bx, sw - bw - 10))
        if tail_dir == "down":
            by = int(mascot_y) - bh - 4
        else:
            by = int(mascot_y) + SIZE + 4
        by = max(10, min(by, sh - bh - 50))

        top = tk.Toplevel(self.root)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        top.attributes("-transparentcolor", "#000001")
        top.config(bg="#000001")
        top.geometry(f"{bw}x{bh}+{bx}+{by}")

        canvas = tk.Canvas(top, width=bw, height=bh, bg="#000001", highlightthickness=0, bd=0)
        canvas.pack()
        tk_img = ImageTk.PhotoImage(im)
        top._img_ref = tk_img
        self._tk_img_ref = tk_img
        canvas.create_image(0, 0, anchor="nw", image=tk_img)
        canvas.bind("<Button-1>", lambda e: self.destroy_bubble())

        self.bubble_win = top
        self._bubble_w = bw
        self._bubble_h = bh
        self._bubble_tail_dir = tail_dir

        duration = max(3500, min(10000, 2500 + len(text) * 75))
        self.bubble_after = self.root.after(duration, self.destroy_bubble)

    def update_position(self, mascot_x: float, mascot_y: float, sw: int, sh: int):
        if self.bubble_win and self._bubble_w > 0:
            try:
                bx = int(mascot_x) + SIZE // 2 - self._bubble_w // 2
                bx = max(10, min(bx, sw - self._bubble_w - 10))
                if self._bubble_tail_dir == 'down':
                    by = int(mascot_y) - self._bubble_h - 4
                else:
                    by = int(mascot_y) + SIZE + 4
                by = max(10, min(by, sh - self._bubble_h - 50))
                self.bubble_win.geometry(f"+{bx}+{by}")
            except Exception:
                pass

    def destroy_bubble(self):
        if self.bubble_after:
            try:
                self.root.after_cancel(self.bubble_after)
            except Exception:
                pass
            self.bubble_after = None
        if self.bubble_win:
            try:
                self.bubble_win.destroy()
            except Exception:
                pass
            self.bubble_win = None
            self._bubble_w = 0
            self._bubble_h = 0
            self._tk_img_ref = None
