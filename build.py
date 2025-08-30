#!/usr/bin/env python3
"""
构建脚本 - 用于打包可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd, cwd=None):
    """运行命令"""
    print(f"运行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"命令执行失败: {result.stderr}")
        return False
    print(f"命令输出: {result.stdout}")
    return True


def install_dependencies():
    """安装依赖"""
    print("=== 安装依赖 ===")
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt"):
        return False
    
    # 安装PyInstaller
    if not run_command(f"{sys.executable} -m pip install pyinstaller"):
        return False
    
    return True


def build_gui():
    """构建GUI版本"""
    print("=== 构建GUI版本 ===")
    
    # 排除不必要的模块以减小文件大小
    excludes = [
        "--exclude-module", "numpy",
        "--exclude-module", "scipy",
        "--exclude-module", "matplotlib",
        "--exclude-module", "pandas",
        "--exclude-module", "jupyter",
        "--exclude-module", "IPython",
        "--exclude-module", "notebook",
        "--exclude-module", "sklearn",
        "--exclude-module", "tensorflow",
        "--exclude-module", "torch",
        "--exclude-module", "cv2",
        "--exclude-module", "PIL.ImageQt",
        "--exclude-module", "PyQt5",
        "--exclude-module", "PyQt6",
        "--exclude-module", "PySide2",
        "--exclude-module", "PySide6"
    ]
    
    cmd = [
        f"{sys.executable}", "-m", "PyInstaller",
        "--windowed",
        "--name", "华科选课助手",
        "--distpath", "dist",
        "--workpath", "build",
        "--clean"
    ] + excludes + [
        "--icon=icon.ico" if os.path.exists("icon.ico") else "",
        "main.py"
    ]
    
    cmd = " ".join(filter(None, cmd))
    return run_command(cmd)


def build_cli():
    """构建CLI版本"""
    print("=== 构建CLI版本 ===")
    
    # 排除不必要的模块以减小文件大小
    excludes = [
        "--exclude-module", "numpy",
        "--exclude-module", "scipy",
        "--exclude-module", "matplotlib",
        "--exclude-module", "pandas",
        "--exclude-module", "jupyter",
        "--exclude-module", "IPython",
        "--exclude-module", "notebook",
        "--exclude-module", "sklearn",
        "--exclude-module", "tensorflow",
        "--exclude-module", "torch",
        "--exclude-module", "cv2",
        "--exclude-module", "customtkinter",
        "--exclude-module", "tkinter",
        "--exclude-module", "PIL.ImageQt",
        "--exclude-module", "PyQt5",
        "--exclude-module", "PyQt6",
        "--exclude-module", "PySide2",
        "--exclude-module", "PySide6"
    ]
    
    cmd = [
        f"{sys.executable}", "-m", "PyInstaller",
        "--console",
        "--name", "华科选课助手-CLI",
        "--distpath", "dist",
        "--workpath", "build",
        "--clean"
    ] + excludes + [
        "cli.py"
    ]
    
    cmd = " ".join(cmd)
    return run_command(cmd)


def clean_build():
    """清理构建文件"""
    print("=== 清理构建文件 ===")
    
    dirs_to_clean = ["build", "__pycache__"]
    files_to_clean = ["*.spec"]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"删除目录: {dir_name}")
    
    import glob
    for pattern in files_to_clean:
        for file_path in glob.glob(pattern):
            os.remove(file_path)
            print(f"删除文件: {file_path}")


def create_release_package():
    """创建发布包"""
    print("=== 创建发布包 ===")
    
    release_dir = Path("release")
    if release_dir.exists():
        shutil.rmtree(release_dir)
    
    release_dir.mkdir()
    
    # 复制可执行文件
    dist_dir = Path("dist")
    if dist_dir.exists():
        for file in dist_dir.glob("*"):
            if file.is_file():
                shutil.copy2(file, release_dir)
                print(f"复制: {file} -> {release_dir}")
    
    # 复制文档
    docs = ["README.md", "requirements.txt"]
    for doc in docs:
        if os.path.exists(doc):
            shutil.copy2(doc, release_dir)
            print(f"复制: {doc} -> {release_dir}")
    
    # 创建使用说明
    usage_text = """NCC选课助手 使用说明

文件说明:
- NCC选课助手.exe: GUI版本（推荐）
- NCC选课助手-CLI.exe: 命令行版本
- README.md: 详细说明文档
- requirements.txt: Python依赖包列表

使用方法:
1. 双击"NCC选课助手.exe"启动GUI版本
2. 或者在命令行中运行"NCC选课助手-CLI.exe"使用命令行版本

注意事项:
- 首次运行可能需要几秒钟启动时间
- 如果遇到问题，请查看README.md
- 使用时请遵守学校相关规定

版本: v1.0.0
"""
    
    with open(release_dir / "使用说明.txt", "w", encoding="utf-8") as f:
        f.write(usage_text)
    
    print(f"发布包已创建在: {release_dir}")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        command = "all"
    
    if command in ["deps", "all"]:
        if not install_dependencies():
            print("依赖安装失败")
            return 1
    
    if command in ["gui", "all"]:
        if not build_gui():
            print("GUI构建失败")
            return 1
    
    if command in ["cli", "all"]:
        if not build_cli():
            print("CLI构建失败")
            return 1
    
    if command in ["package", "all"]:
        create_release_package()
    
    if command in ["clean"]:
        clean_build()
    
    if command == "all":
        print("\\n=== 构建完成 ===")
        print("可执行文件位于 dist/ 目录")
        print("发布包位于 release/ 目录")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
