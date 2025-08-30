"""
工具函数模块
"""

import os
import yaml
import json
from typing import Dict, Any, Optional
from config import Config


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or Config.CONFIG_FILE
        self.config_data = {}
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.config_data = {}
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config_data.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        self.config_data[key] = value
        self.save_config()
    
    def get_user_token(self) -> Optional[str]:
        """获取用户Token"""
        return self.get('user_token')
    
    def set_user_token(self, token: str):
        """保存用户Token"""
        self.set('user_token', token)
    
    def get_window_geometry(self) -> Optional[str]:
        """获取窗口几何信息"""
        return self.get('window_geometry')
    
    def set_window_geometry(self, geometry: str):
        """保存窗口几何信息"""
        self.set('window_geometry', geometry)
    
    def get_theme(self) -> str:
        """获取主题设置"""
        return self.get('theme', 'dark')
    
    def set_theme(self, theme: str):
        """保存主题设置"""
        self.set('theme', theme)


class Logger:
    """简单日志记录器"""
    
    @staticmethod
    def info(message: str):
        """信息日志"""
        print(f"[INFO] {message}")
    
    @staticmethod
    def warning(message: str):
        """警告日志"""
        print(f"[WARNING] {message}")
    
    @staticmethod
    def error(message: str):
        """错误日志"""
        print(f"[ERROR] {message}")


def format_course_info(course) -> str:
    """格式化课程信息"""
    return f"""课程ID: {course.course_id}
课程代码: {course.course_code}
课程名称: {course.course_name}
学期: {course.semester_name}
专业: {course.major}
学分: {course.credit}
学时: {course.credit_hour}
已选/可选: {course.selected}/{course.optional}
开课时间: {course.c_start_date} - {course.c_end_date}
状态: {course.status}
"""


def validate_course_id(course_id_str: str) -> int:
    """验证并转换课程ID"""
    try:
        course_id = int(course_id_str.strip())
        if course_id <= 0:
            raise ValueError("课程ID必须大于0")
        return course_id
    except ValueError:
        raise ValueError("课程ID必须是有效的正整数")


def validate_interval(interval_str: str) -> float:
    """验证并转换时间间隔"""
    try:
        interval = float(interval_str.strip())
        if interval < 0.1:
            raise ValueError("时间间隔不能小于0.1秒")
        if interval > 60:
            raise ValueError("时间间隔不能大于60秒")
        return interval
    except ValueError as e:
        if "could not convert" in str(e):
            raise ValueError("时间间隔必须是有效的数字")
        raise e


def safe_get_attr(obj, attr: str, default: Any = ""):
    """安全获取对象属性"""
    try:
        return getattr(obj, attr, default)
    except:
        return default


def truncate_text(text: str, max_length: int = 50) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def ensure_dir_exists(file_path: str):
    """确保目录存在"""
    dir_path = os.path.dirname(file_path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)


# 全局配置管理器实例
config_manager = ConfigManager()
