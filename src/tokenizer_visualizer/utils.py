"""Utility functions for tokenizer visualization."""

PALETTE = [
    (249, 38, 114),
    (253, 151, 31),
    (230, 219, 116),
    (166, 226, 46),
    (102, 217, 239),
    (174, 129, 255),
]

LIGHT_FG = (248, 248, 242)
DARK_FG = (39, 40, 34)


def luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def pick_foreground(bg: tuple[int, int, int]) -> tuple[int, int, int]:
    return DARK_FG if luminance(bg) >= 160 else LIGHT_FG


def normalize_offsets(text: str, offsets: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not offsets:
        return offsets
    max_end = max(end for _, end in offsets)
    if max_end <= len(text):
        return offsets

    mapping: dict[int, int] = {}
    byte_index = 0
    for char_index, ch in enumerate(text):
        for _ in ch.encode("utf-8"):
            mapping[byte_index] = char_index
            byte_index += 1
    mapping[byte_index] = len(text)

    normalized = []
    for start, end in offsets:
        if start not in mapping or end not in mapping:
            raise ValueError("Invalid byte offsets")
        normalized.append((mapping[start], mapping[end]))
    return normalized
