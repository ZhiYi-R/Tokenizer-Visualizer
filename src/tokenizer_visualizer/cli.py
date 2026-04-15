"""CLI tokenizer visualizer (original ANSI-color version)."""

import argparse
import sys

from tokenizers import Tokenizer

from tokenizer_visualizer.utils import PALETTE, LIGHT_FG, DARK_FG, normalize_offsets, luminance


def pick_foreground(bg: tuple[int, int, int]) -> tuple[int, int, int]:
    return DARK_FG if luminance(bg) >= 160 else LIGHT_FG


def ansi_span(text: str, fg: tuple[int, int, int], bg: tuple[int, int, int]) -> str:
    fr, fg_, fb = fg
    br, bg_, bb = bg
    return f"\x1b[48;2;{br};{bg_};{bb};38;2;{fr};{fg_};{fb};1m{text}\x1b[0m"


def colorize_text(text: str, offsets: list[tuple[int, int]]) -> str:
    try:
        normalized = normalize_offsets(text, offsets)
    except ValueError:
        return text

    parts: list[str] = []
    last_end = 0
    color_index = 0
    for start, end in normalized:
        if (start, end) == (0, 0):
            continue
        if start < last_end:
            continue
        parts.append(text[last_end:start])
        span = text[start:end]
        bg = PALETTE[color_index % len(PALETTE)]
        fg = pick_foreground(bg)
        parts.append(ansi_span(span, fg, bg))
        last_end = end
        color_index += 1
    parts.append(text[last_end:])
    return "".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Tokenizer visualizer")
    parser.add_argument(
        "-t",
        "--tokenizer",
        default="tokenizer.json",
        help="Path to tokenizer JSON file",
    )
    parser.add_argument("text", nargs="*", help="Text to tokenize (default: stdin)")
    args = parser.parse_args()

    try:
        tokenizer = Tokenizer.from_file(args.tokenizer)
    except Exception as exc:
        print(f"Failed to load {args.tokenizer}: {exc}", file=sys.stderr)
        return 1

    text = " ".join(args.text) if args.text else sys.stdin.readline().rstrip("\r\n")
    encoding = tokenizer.encode(text)
    colorized = colorize_text(text, encoding.offsets)
    print(f"分词结果：{colorized}\nToken消耗: {len(encoding.ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
