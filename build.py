#!/usr/bin/env python3
"""Nuitka build script for tokenizer-visualizer."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def build_target(entry: Path, project_root: Path, build_dir: Path, dist_dir: Path, onefile: bool) -> int:
    name = "tokenizer-visualizer"
    output_name = name
    if sys.platform == "win32":
        output_name += ".exe"

    sub_build = build_dir / ("onefile" if onefile else "standalone")

    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
    ]
    if onefile:
        cmd.extend([
            "--onefile",
            "--onefile-tempdir-spec=%CACHE_DIR%/tokenizer-visualizer",
        ])
    cmd.extend([
        "--enable-plugin=pyside6",
        "--include-qt-plugins=platformthemes,imageformats",
        "--static-libpython=no",
        f"--output-dir={sub_build}",
        f"--output-filename={name}",
        "--nofollow-import-to=tkinter",
        "--jobs=4",
        str(entry),
    ])

    if sys.platform == "win32":
        cmd.append("--windows-console-mode=disable")
        icon_path = project_root / "assets" / "icon.ico"
        if icon_path.exists():
            cmd.append(f"--windows-icon-from-ico={icon_path}")
    elif sys.platform == "darwin":
        cmd.append("--macos-disable-console")
        icon_path = project_root / "assets" / "icon.icns"
        if icon_path.exists():
            cmd.append(f"--macos-app-icon={icon_path}")
    else:
        # Linux
        if onefile:
            cmd.append("--disable-console")
        icon_path = project_root / "assets" / "icon.png"
        if icon_path.exists():
            cmd.append(f"--linux-icon={icon_path}")

    env = dict(os.environ)
    env.setdefault("LDFLAGS", "-L/usr/lib/gcc/x86_64-redhat-linux/15")

    print("\n" + "=" * 60)
    print(f"Building {'onefile' if onefile else 'standalone'} target")
    print("=" * 60)
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=project_root, env=env)
    if result.returncode != 0:
        return result.returncode

    # Collect output
    if onefile:
        output = sub_build / output_name
        if output.exists():
            # Place with a temporary extension so main() can move it into a subfolder
            dest = dist_dir / f"{output_name}.bin"
            shutil.copy2(str(output), str(dest))
            print(f"Onefile build succeeded: {dest}")
        else:
            print("Onefile output not found.", file=sys.stderr)
            return 1
    else:
        # Standalone: Nuitka puts the result under main.dist/ (because entry is main.py)
        dist_sub = sub_build / "main.dist"
        if dist_sub.exists():
            dest = dist_dir / f"{name}-standalone"
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(str(dist_sub), str(dest))
            # Copy executable with a clean name
            exe_src = dest / output_name
            if exe_src.exists():
                exe_dest = dest / output_name
                if exe_dest != exe_src:
                    shutil.move(str(exe_src), str(exe_dest))
            print(f"Standalone build succeeded: {dest}")
        else:
            print("Standalone output not found.", file=sys.stderr)
            return 1

    return 0


def main() -> int:
    project_root = Path(__file__).parent.resolve()
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"

    # Clean previous builds
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    build_dir.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)

    entry = project_root / "src" / "tokenizer_visualizer" / "main.py"
    if not entry.exists():
        print(f"Entry file not found: {entry}", file=sys.stderr)
        return 1

    # Build onefile
    rc = build_target(entry, project_root, build_dir, dist_dir, onefile=True)
    if rc != 0:
        return rc

    # Build standalone (folder)
    rc = build_target(entry, project_root, build_dir, dist_dir, onefile=False)
    if rc != 0:
        return rc

    # Package onefile with external data directories into its own release folder
    pkg_name = "tokenizer-visualizer"
    onefile_pkg = dist_dir / pkg_name
    onefile_pkg.mkdir(parents=True, exist_ok=True)
    onefile_bin = dist_dir / (f"{pkg_name}.exe.bin" if sys.platform == "win32" else f"{pkg_name}.bin")
    onefile_out = f"{pkg_name}.exe" if sys.platform == "win32" else pkg_name
    if onefile_bin.exists():
        shutil.move(str(onefile_bin), str(onefile_pkg / onefile_out))
    for data_dir in ["i18n", "tokenizer"]:
        src = project_root / data_dir
        dst = onefile_pkg / data_dir
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(str(src), str(dst))
            print(f"Copied {data_dir}/ to {onefile_pkg}/")

    # Also copy data dirs into standalone folder so it is self-contained
    standalone_pkg = dist_dir / "tokenizer-visualizer-standalone"
    for data_dir in ["i18n", "tokenizer"]:
        src = project_root / data_dir
        dst = standalone_pkg / data_dir
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(str(src), str(dst))
            print(f"Copied {data_dir}/ to {standalone_pkg}/")

    print("\n" + "=" * 60)
    print("All builds completed successfully.")
    print(f"Outputs are in: {dist_dir}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
