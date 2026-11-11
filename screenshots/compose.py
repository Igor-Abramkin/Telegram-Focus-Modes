"""Two app screenshots side by side in showtime's iPhone 17 Pro frame, on its Vivid background, 2200 x 1600.

  compose.py LEFT.png RIGHT.png OUT.png
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SHOWTIME = Path.home() / "showtime"
CANVAS = (2200, 1600)
PHONE_WIDTH = 820
PHONE_TOP = 110

# Apple's iPhone 17 Pro bezel (Apple Design Resources, Product Bezels). Not redistributed: kept next to the video work.
BEZEL = Path(__file__).resolve().parent.parent / "video/bezels/iphone-17-pro-silver.png"
phone = {"screen_insets": [69, 72, 69, 72], "screen_radius_fraction": [0.09, 0.042]}
gradients = json.loads((SHOWTIME / "assets/showtime/gradients.json").read_text())
gradients = gradients if isinstance(gradients, list) else gradients.get("gradients", gradients.get("palettes"))
palette = next(g for g in gradients if g["id"] == "vivid")["palette"]


def hex_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def background():
    # A soft four-corner gradient from the palette, blurred like showtime's backdrops.
    small = Image.new("RGB", (2, 2))
    corners = [hex_rgb(c) for c in palette]
    small.putpixel((0, 0), corners[0])
    small.putpixel((1, 0), corners[1])
    small.putpixel((0, 1), corners[3])
    small.putpixel((1, 1), corners[2])
    return small.resize(CANVAS, Image.BICUBIC).filter(ImageFilter.GaussianBlur(60))


def framed(screenshot_path):
    frame = Image.open(BEZEL).convert("RGBA")
    top, right, bottom, left = phone["screen_insets"]
    screen_w = frame.width - left - right
    screen_h = frame.height - top - bottom
    shot = Image.open(screenshot_path).convert("RGBA").resize((screen_w, screen_h), Image.LANCZOS)
    radius = round(min(screen_w * phone["screen_radius_fraction"][0], screen_h * phone["screen_radius_fraction"][1]))
    mask = Image.new("L", (screen_w, screen_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, screen_w - 1, screen_h - 1), radius=radius, fill=255)
    device = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    device.paste(shot, (left, top), mask)
    device.alpha_composite(frame)
    # The frame image keeps a nearly transparent box around the device; drop it so it casts no shadow.
    device.putalpha(device.getchannel("A").point(lambda a: 0 if a < 24 else a))
    scale = PHONE_WIDTH / device.width
    return device.resize((PHONE_WIDTH, round(device.height * scale)), Image.LANCZOS)


def main():
    left_path, right_path, out_path = sys.argv[1:4]
    canvas = background().convert("RGBA")
    gap = CANVAS[0] // 2
    for index, path in enumerate((left_path, right_path)):
        device = framed(path)
        x = gap * index + (gap - device.width) // 2
        # Blur on a padded canvas, or the shadow is cut off at the phone's bounding box.
        pad = 100
        alpha = Image.new("L", (device.width + 2 * pad, device.height + 2 * pad), 0)
        alpha.paste(device.getchannel("A").point(lambda a: int(a * 0.22)), (pad, pad))
        shadow = Image.new("RGBA", alpha.size, (0, 0, 0, 0))
        shadow.putalpha(alpha.filter(ImageFilter.GaussianBlur(28)))
        canvas.alpha_composite(shadow, (x - pad, PHONE_TOP + 18 - pad))
        canvas.alpha_composite(device, (x, PHONE_TOP))
    canvas.convert("RGB").save(out_path, optimize=True)
    print(out_path)


if __name__ == "__main__":
    main()
