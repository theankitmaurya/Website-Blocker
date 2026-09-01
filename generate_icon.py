"""Script to generate high-resolution application icons for Website Blocker."""
from pathlib import Path
from PIL import Image, ImageDraw

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

def create_shield_icon(size: int = 512) -> Image.Image:
    """Draws a premium shield/focus icon on transparent background."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Margin and coordinates
    m = int(size * 0.08)
    w, h = size - 2 * m, size - 2 * m
    cx, cy = size / 2, size / 2

    # Draw rounded background circle/squircle
    r = int(size * 0.22)
    draw.rounded_rectangle(
        [m, m, size - m, size - m],
        radius=r,
        fill=(17, 19, 24, 255),
        outline=(124, 92, 252, 220),
        width=int(size * 0.025),
    )

    # Draw inner shield geometry
    shield_top = int(size * 0.24)
    shield_bottom = int(size * 0.78)
    shield_left = int(size * 0.26)
    shield_right = int(size * 0.74)
    mid_x = int(size * 0.50)
    mid_y = int(size * 0.52)

    shield_pts = [
        (shield_left, shield_top),
        (shield_right, shield_top),
        (shield_right, mid_y),
        (mid_x, shield_bottom),
        (shield_left, mid_y),
    ]

    # Gradient fill emulation
    draw.polygon(shield_pts, fill=(124, 92, 252, 255), outline=(167, 139, 250, 255))

    # Inner lock / checkmark geometry in crisp white
    lock_cx = mid_x
    lock_cy = int(size * 0.46)
    body_w = int(size * 0.18)
    body_h = int(size * 0.14)

    # Lock shackle (arc/loop)
    shackle_r = int(size * 0.06)
    draw.ellipse(
        [lock_cx - shackle_r, lock_cy - int(size * 0.12), lock_cx + shackle_r, lock_cy + int(size * 0.02)],
        outline=(255, 255, 255, 255),
        width=int(size * 0.035),
    )

    # Lock body
    draw.rounded_rectangle(
        [lock_cx - body_w // 2, lock_cy - int(size * 0.02), lock_cx + body_w // 2, lock_cy + body_h],
        radius=int(size * 0.025),
        fill=(255, 255, 255, 255),
    )

    # Keyhole
    kh_r = int(size * 0.022)
    draw.ellipse(
        [lock_cx - kh_r, lock_cy + int(size * 0.015), lock_cx + kh_r, lock_cy + int(size * 0.055)],
        fill=(124, 92, 252, 255),
    )

    return img

def main():
    icon_img = create_shield_icon(512)
    png_path = ASSETS_DIR / "icon.png"
    ico_path = ASSETS_DIR / "icon.ico"

    icon_img.save(png_path, format="PNG")

    # Generate multi-resolution .ico (16, 24, 32, 48, 64, 128, 256)
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icon_img.save(ico_path, format="ICO", sizes=sizes)
    print("Icons generated successfully in assets folder.")

if __name__ == "__main__":
    main()
