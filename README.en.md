# Tokenizer Visualizer

**English** | [中文](README.md)

A beautiful PySide6-based tokenizer behavior visualizer with multi-model switching, dark/light themes, i18n support, and high-performance long-text rendering.

![icon](assets/icon_256.png)

## Features

- **Multi-model support**: Automatically scans the `tokenizer/` directory for tokenizers; switch models with one click to compare tokenization behavior
- **Real-time visualization**: Instant tokenization as you type, with each token shown as a colored rounded block; spaces and newlines are clearly visible
- **Theme switching**: Supports System, Light, and Dark modes
- **Multi-language**: Built-in Chinese and English UI with automatic system-language detection
- **High-performance rendering**: Custom viewport-based canvas enables smooth scrolling for texts with tens of thousands of tokens
- **Per-line statistics**: Dynamically counts tokens per visual line based on actual word-wrap
- **Hover tooltips**: Hover over a token to see its index, text content, and ID in a rich-text tooltip

## Running

### Development

```bash
uv run tokenizer-visualizer
```

or

```bash
uv run python -m tokenizer_visualizer
```

### Local packaging

```bash
uv run python build.py
```

After packaging, two artifacts will appear under `dist/`:

- `tokenizer-visualizer/` — onefile edition (recommended for distribution)
- `tokenizer-visualizer-standalone/` — folder edition (faster startup)

## Project structure

```
.
├── assets/                    # App icons
├── i18n/                      # i18n files
│   ├── en.json
│   └── zh.json
├── src/tokenizer_visualizer/  # Main source code
│   ├── main.py
│   ├── app.py
│   ├── widgets.py
│   ├── i18n.py
│   └── utils.py
├── tokenizer/                 # Tokenizer model files
├── build.py                   # Nuitka build script
├── generate_icon.py           # Icon generation script
└── pyproject.toml
```

## Adding custom models

Place your `tokenizer.json` under `tokenizer/{model_id}.json` and restart the app; it will be detected automatically.

## GitHub Actions

The repository includes a CI workflow. Pushing a `v*` tag will automatically build and release compressed packages for:

- Linux (`.tar.gz`)
- Windows (`.zip`)
- macOS Intel (`.tar.gz`)
- macOS Apple Silicon (`.tar.gz`)

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
