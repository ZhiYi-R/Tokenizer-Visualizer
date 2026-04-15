#!/usr/bin/env python3
"""Generate a clean, modern app icon for tokenizer-visualizer."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def blend(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def radial_gradient(size, center, c_inner, c_outer):
    w, h = size
    cx, cy = center
    max_dist = (max(cx, w - cx) ** 2 + max(cy, h - cy) ** 2) ** 0.5
    img = Image.new("RGB", size)
    for y in range(h):
        for x in range(w):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / max_dist
            t = d ** 0.8
            col = blend(c_inner, c_outer, t)
            img.putpixel((x, y), col)
    return img.convert("RGBA")


def generate_icon(size=512):
    # Deep elegant radial background
    bg = radial_gradient(
        (size, size),
        (size // 2, size // 3),
        hex_to_rgb("#8b5cf6"),   # violet 500
        hex_to_rgb("#1e1b4b"),   # indigo 950
    )

    radius = size // 4
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=radius, fill=255
    )

    # Soft inner shadow
    inv = Image.new("L", (size, size), 255)
    ImageDraw.Draw(inv).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=radius, fill=0
    )
    blur = inv.filter(ImageFilter.GaussianBlur(radius=12))
    shadow = Image.composite(
        Image.new("RGBA", (size, size), (0, 0, 0, 70)),
        Image.new("RGBA", (size, size), (0, 0, 0, 0)),
        blur,
    )
    bg = Image.alpha_composite(bg, shadow)

    # Soft top gloss
    gloss = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(gloss).rounded_rectangle(
        [10, 10, size - 11, size // 2 - 6], radius=radius // 2, fill=(255, 255, 255, 18)
    )
    bg = Image.alpha_composite(bg, gloss)

    palette = [
        (244, 114, 182),  # pink 400
        (45, 212, 191),   # teal 400
        (250, 204, 21),   # yellow 400
    ]

    block_h = int(size * 0.22)
    gap = int(size * 0.04)
    total = int(size * 0.60)

    widths = [int(total * 0.28), int(total * 0.40), int(total * 0.32)]
    actual = sum(widths) + gap * 2
    start_x = (size - actual) // 2
    block_y = (size - block_h) // 2
    r = block_h // 3

    # Drop shadows
    drop = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dd = ImageDraw.Draw(drop)
    bx = start_x
    for w in widths:
        dd.rounded_rectangle(
            [bx + 4, block_y + 5, bx + w + 4, block_y + block_h + 5],
            radius=r, fill=(0, 0, 0, 60)
        )
        bx += w + gap
    drop = drop.filter(ImageFilter.GaussianBlur(radius=5))
    bg = Image.alpha_composite(bg, drop)

    draw = ImageDraw.Draw(bg)

    # Collect highlight rects for later compositing
    hl_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(hl_layer)

    bx = start_x
    for i, w in enumerate(widths):
        col = palette[i]

        # Main solid block
        draw.rounded_rectangle(
            [bx, block_y, bx + w, block_y + block_h],
            radius=r, fill=col
        )

        # Top highlight (will be alpha-composited)
        hdraw.rounded_rectangle(
            [bx + 1, block_y + 1, bx + w - 1, block_y + block_h // 2 - 1],
            radius=r // 2, fill=(255, 255, 255, 50)
        )

        bx += w + gap

    # Composite highlight layer once
    bg = Image.alpha_composite(bg, hl_layer)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(bg, (0, 0), mask)
    return out


def save_png(img, path):
    img.save(path, "PNG")
    print(f"Saved PNG: {path}")


def save_ico(img, path):
    sizes = [256, 128, 64, 48, 32, 16]
    icons = [img.resize((s, s), Image.LANCZOS).convert("RGBA") for s in sizes]
    icons[0].save(path, format="ICO", sizes=[(s, s) for s in sizes])
    print(f"Saved ICO: {path}")


def main():
    assets = Path(__file__).parent / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    icon = generate_icon(size=512)
    save_png(icon, assets / "icon.png")
    save_ico(icon, assets / "icon.ico")
    save_png(icon.resize((256, 256), Image.LANCZOS), assets / "icon_256.png")


if __name__ == "__main__":
    main()
