#!/usr/bin/env python3
"""
NCC选课助手
NCC Course Selection Assistant
"""

import sys
import os
from gui import main

if __name__ == "__main__":
    # 设置程序图标和标题
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller环境
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # 启动GUI
    main()
