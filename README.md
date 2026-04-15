# 分词器可视化工具

[English](README.en.md) | **中文**

一个基于 PySide6 的美观分词器行为可视化工具，支持多模型切换、暗色/亮色主题、多语言以及高性能的长文本渲染。

![icon](assets/icon_256.png)

## 功能特性

- **多模型支持**：自动扫描 `tokenizer/` 目录下的分词器，一键切换对比不同模型的分词行为
- **实时可视化**：输入文本即时分词，每个 token 以彩色圆角块呈现，空格与换行符一目了然
- **主题切换**：支持跟随系统、亮色、暗色三种主题模式
- **多语言**：内置中文与英文界面，自动检测系统语言
- **高性能渲染**：自定义 Viewport-based 画布，支持上万 token 的长文本流畅滚动
- **每行统计**：根据视觉换行动态统计每行 token 数量
- **鼠标悬停提示**：悬停 token 时以富文本 tooltip 显示 token 序号、文本内容和 ID

## 运行方式

### 开发运行

```bash
uv run tokenizer-visualizer
```

或

```bash
uv run python -m tokenizer_visualizer
```

### 本地打包

```bash
uv run python build.py
```

打包完成后会在 `dist/` 目录下生成两个产物：

- `tokenizer-visualizer/` —— 单文件版本（推荐分发）
- `tokenizer-visualizer-standalone/` —— 文件夹版本（启动更快）

## 项目结构

```
.
├── assets/                    # 应用图标
├── i18n/                      # 多语言文件
│   ├── en.json
│   └── zh.json
├── src/tokenizer_visualizer/  # 主程序源码
│   ├── main.py
│   ├── app.py
│   ├── widgets.py
│   ├── i18n.py
│   └── utils.py
├── tokenizer/                 # 分词器模型文件
├── build.py                   # Nuitka 打包脚本
├── generate_icon.py           # 图标生成脚本
└── pyproject.toml
```

## 添加自定义模型

将 `tokenizer.json` 文件放入 `tokenizer/{model_id}.json` 目录下，重启程序即可自动识别。

## GitHub Actions

仓库已配置 CI，推送 `v*` 标签后将自动构建并发布以下平台的压缩包：

- Linux (`.tar.gz`)
- Windows (`.zip`)
- macOS Intel (`.tar.gz`)
- macOS Apple Silicon (`.tar.gz`)

## License

本项目采用 [GNU General Public License v3.0](LICENSE) 开源协议。
