"""Internationalization support with JSON language files."""

import json
import locale
import pathlib
import sys
from typing import Any


class I18n:
    _instance: "I18n | None" = None

    def __new__(cls) -> "I18n":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data: dict[str, str] = {}
            cls._instance._lang = "en"
        return cls._instance

    def load(self, lang: str | None = None) -> None:
        if lang is None:
            lang = self._detect_system_language()
        self._lang = lang
        base = self._find_i18n_dir()
        path = base / f"{lang}.json"
        if not path.exists():
            path = base / "en.json"
        with open(path, encoding="utf-8") as f:
            self._data = json.load(f)

    @staticmethod
    def _find_i18n_dir() -> pathlib.Path:
        # When frozen (Nuitka), look next to the executable first (external data dir)
        candidates = [
            pathlib.Path(sys.executable).parent,
            pathlib.Path(sys.argv[0]).parent.resolve(),
        ]
        for cand in candidates:
            ext_path = cand / "i18n"
            if ext_path.exists():
                return ext_path
        # Development layout: src/tokenizer_visualizer/i18n.py -> project_root/i18n
        dev_path = pathlib.Path(__file__).parent.parent.parent / "i18n"
        if dev_path.exists():
            return dev_path
        # Fallback frozen internal layout
        return pathlib.Path(__file__).parent.parent / "i18n"

    @staticmethod
    def _detect_system_language() -> str:
        try:
            loc, _ = locale.getdefaultlocale()
            if loc and loc.lower().startswith("zh"):
                return "zh"
        except Exception:
            pass
        return "en"

    def t(self, key: str, **kwargs: Any) -> str:
        text = self._data.get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                pass
        return text

    @property
    def lang(self) -> str:
        return self._lang


def tr(key: str, **kwargs: Any) -> str:
    return I18n().t(key, **kwargs)
