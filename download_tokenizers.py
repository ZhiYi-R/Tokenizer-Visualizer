#!/usr/bin/env python3
"""Download tokenizer.json files from Hugging Face for popular open-source LLMs.

Covers trending models released in 2025–2026 as well as classic widely-used
tokenizers. Run this script on a machine with internet access:

    uv run python download_tokenizers.py

Some models are "gated" (require accepting a license on Hugging Face).
To skip gated models automatically:

    uv run python download_tokenizers.py --skip-gated

For gated models you want to keep, accept the license on the model card page
and run `huggingface-cli login` before executing this script.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from tokenizers import Tokenizer

# Models known to require Hugging Face license acceptance (gated repos).
# You can still download them after accepting the license and logging in.
GATED_MODELS: set[str] = {
    "meta-llama/Llama-3.1-8B-Instruct",
    "meta-llama/Llama-3.2-1B",
    "meta-llama/Llama-4-Scout-17B-16E-Instruct",
    "meta-llama/Llama-4-Maverick-17B-128E-Instruct",
    "google/gemma-2-2b-it",
    "google/gemma-3-1b-it",
    "google/gemma-3-4b-it",
    "google/gemma-3-12b-it",
    "google/gemma-3-27b-it",
    "mistralai/Mistral-Large-Instruct-2407",
    "nvidia/Nemotron-Cascade-2-30B-A3B",
}

MODELS: dict[str, str] = {
    # === 2026 年发布 / Trending ===
    # Qwen 3.5 系列 (阿里, 2026-02/03)
    "Qwen3.5-397B": "Qwen/Qwen3.5-397B-A17B",
    "Qwen3.5-122B": "Qwen/Qwen3.5-122B-A10B",
    "Qwen3.5-27B": "Qwen/Qwen3.5-27B",
    "Qwen3.5-9B": "Qwen/Qwen3.5-9B",
    "Qwen3.5-4B": "Qwen/Qwen3.5-4B",

    # GLM-5 (智谱, 2026-02)
    "GLM-5": "zai-org/GLM-5",

    # Llama 4 系列 (Meta, 2025-04)  [GATED]
    "Llama-4-Scout": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
    "Llama-4-Maverick": "meta-llama/Llama-4-Maverick-17B-128E-Instruct",

    # Devstral 2 (Mistral, 2025-12)
    "Devstral-2-123B": "mistralai/Devstral-2-123B-Instruct-2512",
    "Devstral-Small-2": "mistralai/Devstral-Small-2-24B-Instruct-2512",

    # === 2025 年发布 / 热门 ===
    # DeepSeek 系列
    "DeepSeek-R1-0528": "deepseek-ai/DeepSeek-R1-0528",
    "DeepSeek-V3": "deepseek-ai/DeepSeek-V3",
    "DeepSeek-R1-0528-Qwen3-8B": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",

    # Qwen 3 系列
    "Qwen3-8B": "Qwen/Qwen3-8B",

    # Google Gemma 3 系列 (2025-03)  [GATED]
    "Gemma-3-1B": "google/gemma-3-1b-it",
    "Gemma-3-4B": "google/gemma-3-4b-it",
    "Gemma-3-12B": "google/gemma-3-12b-it",
    "Gemma-3-27B": "google/gemma-3-27b-it",

    # Mistral Large 2 (2024-07, 仍是 2025–2026 Mistral 旗舰)  [GATED]
    # Note: its tokenizer is the same as Mistral-7B-v0.1, so skipping it
    # does not reduce tokenizer diversity.
    "Mistral-Large-2": "mistralai/Mistral-Large-Instruct-2407",

    # NVIDIA Nemotron Cascade 2 (2025–2026)  [GATED]
    "Nemotron-Cascade-2": "nvidia/Nemotron-Cascade-2-30B-A3B",

    # === 经典常青树 (2023–2024) ===
    "Qwen2.5-1.5B-Instruct": "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen2.5-7B": "Qwen/Qwen2.5-7B",
    "Llama-3.1-8B-Instruct": "meta-llama/Llama-3.1-8B-Instruct",
    "Llama-3.2-1B": "meta-llama/Llama-3.2-1B",
    "Mistral-7B": "mistralai/Mistral-7B-v0.1",
    "Mixtral-8x7B": "mistralai/Mixtral-8x7B-v0.1",
    "GLM-4-9B": "THUDM/glm-4-9b-chat",
    "ChatGLM3-6B": "THUDM/chatglm3-6b",
    "Yi-1.5-9B": "01-ai/Yi-1.5-9B-Chat",
    "MiniCPM3-4B": "OpenBMB/MiniCPM3-4B",
    "InternLM2.5-7B": "internlm/internlm2_5-7b",
}


def _is_gated_error(exc: Exception) -> bool:
    """Heuristic to detect Hugging Face gated-repo errors."""
    msg = str(exc).lower()
    return "gated" in msg or "cannot access" in msg or "401" in msg


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download tokenizer.json files from Hugging Face."
    )
    parser.add_argument(
        "--skip-gated",
        action="store_true",
        help="Skip models that require Hugging Face license acceptance.",
    )
    args = parser.parse_args()

    output_dir = Path(__file__).parent / "tokenizer"
    output_dir.mkdir(parents=True, exist_ok=True)

    success = skipped = failed = 0
    gated_skipped = []

    for name, repo_id in MODELS.items():
        output_path = output_dir / f"{name}.json"
        if output_path.exists():
            print(f"[SKIP] {name}: already exists")
            skipped += 1
            continue

        if args.skip_gated and repo_id in GATED_MODELS:
            print(f"[SKIP-GATED] {name} ({repo_id})")
            gated_skipped.append(name)
            continue

        try:
            print(f"[DOWNLOAD] {name} from {repo_id} ...")
            tokenizer = Tokenizer.from_pretrained(repo_id)
            tokenizer.save(str(output_path))
            print(f"[OK] {name} -> {output_path}")
            success += 1
        except Exception as e:
            if _is_gated_error(e):
                print(
                    f"[GATED] {name}: {e}\n"
                    f"        -> Accept the license at https://huggingface.co/{repo_id}\n"
                    f"        -> Then run: huggingface-cli login"
                )
                gated_skipped.append(name)
            else:
                print(f"[FAIL] {name}: {e}")
                failed += 1

    print(f"\nDone.  OK: {success}  Skipped: {skipped}  Gated: {len(gated_skipped)}  Failed: {failed}")
    if gated_skipped:
        print(f"\nGated models requiring login/license acceptance: {', '.join(gated_skipped)}")
        print("Tip: Re-run with --skip-gated to skip them automatically.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
