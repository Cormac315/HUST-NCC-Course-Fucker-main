"""
GUI界面
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import threading
import io
import time
from typing import List, Optional
from client import HUSTCourseClient
from course import Course
from config import Config
from scheduler import CourseQueue, ScheduledCourseGrabber, CourseTask
from datetime import datetime, timedelta


class CourseSelectionGUI:
    """选课系统GUI"""
    
    def __init__(self):
        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 初始化客户端
        self.client = HUSTCourseClient()
        
        # 创建主窗口
        self.root = ctk.CTk()
        self.root.title("NCC选课助手 - V1.0 by Cormac@CSE")
        self.root.geometry(f"{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
        self.root.resizable(True, True)
        
        # 居中窗口
        self.center_window()
        
        # 数据存储
        self.courses: List[Course] = []
        self.selected_course: Optional[Course] = None
        self.captcha_uuid: Optional[str] = None
        self.auto_select_running = False
        self.user_info: Optional[dict] = None
        self.is_login_view = True  # 当前是否显示登录界面
        
        # 定时选课相关
        self.course_queue = CourseQueue()
        self.scheduler = ScheduledCourseGrabber(self.client, self.course_queue)
        self.courses_loaded = False  # 是否已加载课程列表
        
        # 创建界面
        self.create_widgets()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def center_window(self):
        """居中窗口"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def center_dialog(self, dialog):
        """居中对话框"""
        dialog.update_idletasks()
        # 获取主窗口的位置和大小
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        
        # 设置对话框的最小宽度
        dialog_width = max(dialog.winfo_reqwidth(), 400)  # 最小宽度400像素
        dialog_height = dialog.winfo_reqheight()
        
        # 计算居中位置（相对于主窗口）
        x = main_x + (main_width - dialog_width) // 2
        y = main_y + (main_height - dialog_height) // 2
        
        # 设置对话框位置和大小
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        dialog.minsize(400, dialog_height)  # 设置最小尺寸
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 创建选项卡
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 登录选项卡
        self.login_tab = self.tabview.add("登录")
        self.create_login_tab()
        
        # 课程管理选项卡
        self.course_tab = self.tabview.add("课程管理")
        self.create_course_tab()
        
        # 自动选课选项卡
        self.auto_select_tab = self.tabview.add("自动选课")
        self.create_auto_select_tab()
        
        # 定时选课选项卡
        self.scheduled_tab = self.tabview.add("定时选课")
        self.create_scheduled_tab()
        
        # 设置选项卡
        self.settings_tab = self.tabview.add("设置")
        self.create_settings_tab()
        
        # 默认选择登录选项卡
        self.tabview.set("登录")
    
    def create_login_tab(self):
        """创建登录选项卡"""
        # 创建容器框架
        self.login_container = ctk.CTkFrame(self.login_tab)
        self.login_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建登录表单和用户信息界面
        self.create_login_form()
        self.create_user_info_view()
        
        # 默认显示登录表单
        self.show_login_form()
    
    def create_login_form(self):
        """创建登录表单"""
        # 登录表单框架
        self.login_form_frame = ctk.CTkFrame(self.login_container)
        
        # 标题
        title = ctk.CTkLabel(
            self.login_form_frame, 
            text="NCC选课系统登录", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(20, 30))
        
        # 登录表单内容框架
        login_frame = ctk.CTkFrame(self.login_form_frame)
        login_frame.pack(pady=20, padx=50, fill="x")
        
        # 用户名
        ctk.CTkLabel(login_frame, text="学号:", font=ctk.CTkFont(size=14)).pack(pady=(20, 5))
        self.username_entry = ctk.CTkEntry(
            login_frame, 
            placeholder_text="请输入学号",
            width=300,
            height=35
        )
        self.username_entry.pack(pady=(0, 15))
        
        # 密码
        ctk.CTkLabel(login_frame, text="密码:", font=ctk.CTkFont(size=14)).pack(pady=(0, 5))
        self.password_entry = ctk.CTkEntry(
            login_frame, 
            placeholder_text="请输入密码",
            show="*",
            width=300,
            height=35
        )
        self.password_entry.pack(pady=(0, 15))
        
        # 验证码框架
        captcha_frame = ctk.CTkFrame(login_frame)
        captcha_frame.pack(pady=(0, 20), fill="x", padx=20)
        
        # 验证码标签
        ctk.CTkLabel(captcha_frame, text="验证码:", font=ctk.CTkFont(size=14)).pack(pady=(10, 5))
        
        # 验证码输入和图片框架（居中）
        captcha_input_frame = ctk.CTkFrame(captcha_frame)
        captcha_input_frame.pack(pady=(0, 10))
        
        self.captcha_entry = ctk.CTkEntry(
            captcha_input_frame,
            placeholder_text="请输入验证码",
            width=150,
            height=35
        )
        self.captcha_entry.pack(side="left", padx=(10, 10))
        
        # 验证码图片
        self.captcha_label = tk.Label(captcha_input_frame, text="点击获取验证码", bg="#2b2b2b", fg="white")
        self.captcha_label.pack(side="left", padx=(0, 10))
        self.captcha_label.bind("<Button-1>", lambda e: self.load_captcha())
        
        # 刷新验证码按钮
        refresh_btn = ctk.CTkButton(
            captcha_input_frame,
            text="刷新",
            width=80,
            height=35,
            command=self.load_captcha
        )
        refresh_btn.pack(side="left", padx=(0, 10))
        
        # 登录按钮
        self.login_btn = ctk.CTkButton(
            login_frame,
            text="登录",
            width=200,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.login
        )
        self.login_btn.pack(pady=(0, 20))
        
        # 状态标签
        self.login_status = ctk.CTkLabel(login_frame, text="", text_color="green")
        self.login_status.pack(pady=(0, 20))
        
        # 快速登录框架（使用保存的Token）
        quick_login_frame = ctk.CTkFrame(self.login_form_frame)
        quick_login_frame.pack(pady=20, padx=50, fill="x")
        
        ctk.CTkLabel(quick_login_frame, text="快速登录 (使用Token)", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        self.token_entry = ctk.CTkEntry(
            quick_login_frame,
            placeholder_text="请输入Token（可选）",
            width=400,
            height=35
        )
        self.token_entry.pack(pady=(0, 15))
        
        token_login_btn = ctk.CTkButton(
            quick_login_frame,
            text="使用Token登录",
            width=150,
            height=35,
            command=self.token_login
        )
        token_login_btn.pack(pady=(0, 15))
        
        # 初始加载验证码
        self.load_captcha()
    
    def create_user_info_view(self):
        """创建用户信息视图"""
        # 用户信息框架
        self.user_info_frame = ctk.CTkFrame(self.login_container)
        
        # 标题
        title = ctk.CTkLabel(
            self.user_info_frame,
            text="用户信息",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(20, 30))
        
        # 用户信息内容框架
        info_content_frame = ctk.CTkFrame(self.user_info_frame)
        info_content_frame.pack(pady=20, padx=50, fill="both", expand=True)
        
        # 用户基本信息
        self.user_name_label = ctk.CTkLabel(
            info_content_frame,
            text="",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.user_name_label.pack(pady=(20, 10))
        
        # 用户详细信息框架
        details_frame = ctk.CTkFrame(info_content_frame)
        details_frame.pack(pady=10, padx=20, fill="x")
        
        # 左侧信息
        left_frame = ctk.CTkFrame(details_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)
        
        self.user_id_label = ctk.CTkLabel(left_frame, text="", font=ctk.CTkFont(size=14))
        self.user_id_label.pack(pady=5, anchor="w", padx=10)
        
        self.email_label = ctk.CTkLabel(left_frame, text="", font=ctk.CTkFont(size=14))
        self.email_label.pack(pady=5, anchor="w", padx=10)
        
        self.phone_label = ctk.CTkLabel(left_frame, text="", font=ctk.CTkFont(size=14))
        self.phone_label.pack(pady=5, anchor="w", padx=10)
        
        # 右侧信息
        right_frame = ctk.CTkFrame(details_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)
        
        self.login_time_label = ctk.CTkLabel(right_frame, text="", font=ctk.CTkFont(size=14))
        self.login_time_label.pack(pady=5, anchor="w", padx=10)
        
        self.pwd_exp_label = ctk.CTkLabel(right_frame, text="", font=ctk.CTkFont(size=14))
        self.pwd_exp_label.pack(pady=5, anchor="w", padx=10)
        
        self.role_label = ctk.CTkLabel(right_frame, text="", font=ctk.CTkFont(size=14))
        self.role_label.pack(pady=5, anchor="w", padx=10)
        
        # 注销按钮
        logout_btn = ctk.CTkButton(
            info_content_frame,
            text="注销登录",
            width=150,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="red",
            hover_color="darkred",
            command=self.logout
        )
        logout_btn.pack(pady=30)
    
    def show_login_form(self):
        """显示登录表单"""
        self.user_info_frame.pack_forget()
        self.login_form_frame.pack(fill="both", expand=True)
        self.is_login_view = True
    
    def show_user_info(self):
        """显示用户信息"""
        self.login_form_frame.pack_forget()
        self.user_info_frame.pack(fill="both", expand=True)
        self.is_login_view = False
    
    def update_user_info_display(self):
        """更新用户信息显示"""
        if not self.user_info:
            return
        
        user_data = self.user_info.get("user", {})
        
        # 更新用户名和昵称
        user_name = user_data.get("userName", "")
        nick_name = user_data.get("nickName", "")
        self.user_name_label.configure(text=f"{nick_name} ({user_name})")
        
        # 更新详细信息
        self.user_id_label.configure(text=f"学号: {user_name}")
        self.email_label.configure(text=f"邮箱: {user_data.get('email', '未设置')}")
        self.phone_label.configure(text=f"手机: {user_data.get('phonenumber', '未设置')}")
        
        # 格式化时间
        login_time = user_data.get("loginDate", "")
        if login_time:
            try:
                from datetime import datetime
                # 解析时间字符串
                dt = datetime.fromisoformat(login_time.replace("T", " ").split("+")[0])
                login_time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                login_time_str = login_time
        else:
            login_time_str = "未知"
        
        pwd_exp_time = user_data.get("pwdExpTime", "")
        if pwd_exp_time:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(pwd_exp_time.replace("T", " ").split("+")[0])
                pwd_exp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pwd_exp_str = pwd_exp_time
        else:
            pwd_exp_str = "未知"
        
        self.login_time_label.configure(text=f"登录时间: {login_time_str}")
        self.pwd_exp_label.configure(text=f"密码过期: {pwd_exp_str}")
        
        # 角色信息
        roles = self.user_info.get("roles", [])
        role_names = [role for role in roles if role]
        self.role_label.configure(text=f"角色: {', '.join(role_names) if role_names else '未知'}")
    
    def create_course_tab(self):
        """创建课程管理选项卡"""
        # 顶部按钮框架
        top_frame = ctk.CTkFrame(self.course_tab)
        top_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # 获取课程列表按钮
        get_courses_btn = ctk.CTkButton(
            top_frame,
            text="获取课程列表",
            width=120,
            height=35,
            command=self.get_courses
        )
        get_courses_btn.pack(side="left", padx=(10, 5), pady=10)
        
        # 刷新按钮
        refresh_btn = ctk.CTkButton(
            top_frame,
            text="刷新",
            width=80,
            height=35,
            command=self.refresh_courses
        )
        refresh_btn.pack(side="left", padx=5, pady=10)
        
        # 搜索框
        search_frame = ctk.CTkFrame(top_frame)
        search_frame.pack(side="right", padx=10, pady=10)
        
        ctk.CTkLabel(search_frame, text="搜索:").pack(side="left", padx=(10, 5))
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="课程名称或代码",
            width=200,
            height=35
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.filter_courses)
        
        # 课程列表框架
        list_frame = ctk.CTkFrame(self.course_tab)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 创建Treeview
        columns = ("ID", "课程代码", "课程名称", "学期", "专业", "学分", "已选/可选")
        self.course_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # 设置列标题和宽度
        self.course_tree.heading("ID", text="课程ID")
        self.course_tree.heading("课程代码", text="课程代码")
        self.course_tree.heading("课程名称", text="课程名称")
        self.course_tree.heading("学期", text="学期")
        self.course_tree.heading("专业", text="专业")
        self.course_tree.heading("学分", text="学分")
        self.course_tree.heading("已选/可选", text="已选/可选")
        
        self.course_tree.column("ID", width=80)
        self.course_tree.column("课程代码", width=100)
        self.course_tree.column("课程名称", width=200)
        self.course_tree.column("学期", width=100)
        self.course_tree.column("专业", width=150)
        self.course_tree.column("学分", width=60)
        self.course_tree.column("已选/可选", width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.course_tree.yview)
        self.course_tree.configure(yscrollcommand=scrollbar.set)
        
        # 打包Treeview和滚动条
        self.course_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10, padx=(0, 10))
        
        # 绑定选择事件和右键菜单
        self.course_tree.bind("<<TreeviewSelect>>", self.on_course_select)
        self.course_tree.bind("<Button-3>", self.show_course_context_menu)
        
        # 底部信息框架
        info_frame = ctk.CTkFrame(self.course_tab)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        self.course_info_label = ctk.CTkLabel(
            info_frame,
            text="请先登录并获取课程列表",
            font=ctk.CTkFont(size=12)
        )
        self.course_info_label.pack(pady=10)
    
    def create_auto_select_tab(self):
        """创建自动选课选项卡"""
        # 标题
        title = ctk.CTkLabel(
            self.auto_select_tab,
            text="自动选课",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(20, 30))
        
        # 选课设置框架
        settings_frame = ctk.CTkFrame(self.auto_select_tab)
        settings_frame.pack(fill="x", padx=50, pady=20)
        
        # 课程ID输入
        ctk.CTkLabel(settings_frame, text="课程ID:", font=ctk.CTkFont(size=14)).pack(pady=(20, 5))
        self.course_id_entry = ctk.CTkEntry(
            settings_frame,
            placeholder_text="请输入要选择的课程ID",
            width=300,
            height=35
        )
        self.course_id_entry.pack(pady=(0, 15))
        
        # 选课间隔设置
        ctk.CTkLabel(settings_frame, text="选课间隔 (秒):", font=ctk.CTkFont(size=14)).pack(pady=(0, 5))
        self.interval_entry = ctk.CTkEntry(
            settings_frame,
            placeholder_text=f"默认: {Config.TIME_INTERVAL}",
            width=300,
            height=35
        )
        self.interval_entry.pack(pady=(0, 20))
        
        # 控制按钮框架（居中）
        control_frame = ctk.CTkFrame(self.auto_select_tab)
        control_frame.pack(padx=50, pady=20)
        
        # 开始自动选课按钮
        self.start_auto_btn = ctk.CTkButton(
            control_frame,
            text="开始自动选课",
            width=150,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="green",
            hover_color="darkgreen",
            command=self.start_auto_select
        )
        self.start_auto_btn.pack(side="left", padx=(20, 10), pady=20)
        
        # 停止自动选课按钮
        self.stop_auto_btn = ctk.CTkButton(
            control_frame,
            text="停止自动选课",
            width=150,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="red",
            hover_color="darkred",
            command=self.stop_auto_select,
            state="disabled"
        )
        self.stop_auto_btn.pack(side="left", padx=(10, 20), pady=20)
        
        # 日志框架
        log_frame = ctk.CTkFrame(self.auto_select_tab)
        log_frame.pack(fill="both", expand=True, padx=50, pady=(0, 20))
        
        ctk.CTkLabel(log_frame, text="选课日志:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5), anchor="w", padx=15)
        
        # 日志文本框
        self.log_textbox = ctk.CTkTextbox(log_frame, height=200)
        self.log_textbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 清空日志按钮
        clear_log_btn = ctk.CTkButton(
            log_frame,
            text="清空日志",
            width=100,
            height=30,
            command=self.clear_log
        )
        clear_log_btn.pack(pady=(0, 15))
    
    def create_scheduled_tab(self):
        """创建定时选课选项卡"""
        # 标题
        title = ctk.CTkLabel(
            self.scheduled_tab,
            text="定时选课",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(20, 20))
        
        # 主要内容框架
        main_frame = ctk.CTkFrame(self.scheduled_tab)
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # 左侧：设置区域
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="y", padx=(10, 5), pady=10)
        
        # 时间设置
        time_frame = ctk.CTkFrame(left_frame)
        time_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(time_frame, text="定时设置", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        # 日期选择
        date_frame = ctk.CTkFrame(time_frame)
        date_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(date_frame, text="日期:").pack(side="left", padx=(10, 5))
        
        # 年月日选择
        today = datetime.now()
        
        self.year_var = tk.StringVar(value=str(today.year))
        year_combo = ctk.CTkComboBox(
            date_frame,
            values=[str(today.year + i) for i in range(2)],
            variable=self.year_var,
            width=80
        )
        year_combo.pack(side="left", padx=2)
        
        ctk.CTkLabel(date_frame, text="年").pack(side="left", padx=2)
        
        self.month_var = tk.StringVar(value=str(today.month))
        month_combo = ctk.CTkComboBox(
            date_frame,
            values=[str(i) for i in range(1, 13)],
            variable=self.month_var,
            width=60
        )
        month_combo.pack(side="left", padx=2)
        
        ctk.CTkLabel(date_frame, text="月").pack(side="left", padx=2)
        
        self.day_var = tk.StringVar(value=str(today.day))
        day_combo = ctk.CTkComboBox(
            date_frame,
            values=[str(i) for i in range(1, 32)],
            variable=self.day_var,
            width=60
        )
        day_combo.pack(side="left", padx=2)
        
        ctk.CTkLabel(date_frame, text="日").pack(side="left", padx=(2, 10))
        
        # 时间选择
        time_select_frame = ctk.CTkFrame(time_frame)
        time_select_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(time_select_frame, text="时间:").pack(side="left", padx=(10, 5))
        
        self.hour_var = tk.StringVar(value="08")
        hour_combo = ctk.CTkComboBox(
            time_select_frame,
            values=[f"{i:02d}" for i in range(24)],
            variable=self.hour_var,
            width=60
        )
        hour_combo.pack(side="left", padx=2)
        
        ctk.CTkLabel(time_select_frame, text=":").pack(side="left", padx=2)
        
        self.minute_var = tk.StringVar(value="00")
        minute_combo = ctk.CTkComboBox(
            time_select_frame,
            values=[f"{i:02d}" for i in range(60)],
            variable=self.minute_var,
            width=60
        )
        minute_combo.pack(side="left", padx=2)
        
        ctk.CTkLabel(time_select_frame, text=":").pack(side="left", padx=2)
        
        self.second_var = tk.StringVar(value="00")
        second_combo = ctk.CTkComboBox(
            time_select_frame,
            values=[f"{i:02d}" for i in range(60)],
            variable=self.second_var,
            width=60
        )
        second_combo.pack(side="left", padx=(2, 5))
        
        # 使用当前时间按钮
        use_current_btn = ctk.CTkButton(
            time_select_frame,
            text="当前时间",
            width=80,
            height=30,
            command=self.use_current_time
        )
        use_current_btn.pack(side="left", padx=(5, 10))
        
        # 抢课频率设置
        freq_frame = ctk.CTkFrame(time_frame)
        freq_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(freq_frame, text="抢课间隔(秒):").pack(side="left", padx=(10, 5))
        self.freq_entry = ctk.CTkEntry(
            freq_frame,
            placeholder_text="1.0",
            width=100
        )
        self.freq_entry.pack(side="left", padx=(0, 10))
        
        # 控制按钮
        control_frame = ctk.CTkFrame(left_frame)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(control_frame, text="定时控制", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        self.schedule_btn = ctk.CTkButton(
            control_frame,
            text="设置定时抢课",
            width=120,
            height=35,
            command=self.set_scheduled_grab
        )
        self.schedule_btn.pack(pady=5, padx=10)
        
        self.start_now_btn = ctk.CTkButton(
            control_frame,
            text="立即开始抢课",
            width=120,
            height=35,
            fg_color="green",
            hover_color="darkgreen",
            command=self.start_immediate_grab
        )
        self.start_now_btn.pack(pady=5, padx=10)
        
        self.stop_scheduled_btn = ctk.CTkButton(
            control_frame,
            text="停止抢课",
            width=120,
            height=35,
            fg_color="red",
            hover_color="darkred",
            command=self.stop_scheduled_grab,
            state="disabled"
        )
        self.stop_scheduled_btn.pack(pady=5, padx=10)
        
        # 状态显示
        status_display_frame = ctk.CTkFrame(left_frame)
        status_display_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(status_display_frame, text="状态信息", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        # 当前时间显示
        self.current_time_label = ctk.CTkLabel(
            status_display_frame,
            text="当前时间: --:--:--",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="green"
        )
        self.current_time_label.pack(pady=2, padx=10)
        
        self.scheduled_status_label = ctk.CTkLabel(
            status_display_frame,
            text="状态: 未设置",
            font=ctk.CTkFont(size=12)
        )
        self.scheduled_status_label.pack(pady=2, padx=10)
        
        self.scheduled_time_label = ctk.CTkLabel(
            status_display_frame,
            text="计划时间: 未设置",
            font=ctk.CTkFont(size=12)
        )
        self.scheduled_time_label.pack(pady=2, padx=10)
        
        self.queue_count_label = ctk.CTkLabel(
            status_display_frame,
            text="队列课程: 0",
            font=ctk.CTkFont(size=12)
        )
        self.queue_count_label.pack(pady=(2, 10), padx=10)
        
        # 右侧：抢课队列
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)
        
        # 队列标题和操作
        queue_header = ctk.CTkFrame(right_frame)
        queue_header.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(queue_header, text="抢课队列", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", pady=10)
        
        # 队列操作按钮
        queue_btn_frame = ctk.CTkFrame(queue_header)
        queue_btn_frame.pack(side="right", pady=10, padx=10)
        
        clear_completed_btn = ctk.CTkButton(
            queue_btn_frame,
            text="清除成功",
            width=80,
            height=30,
            command=self.clear_completed_tasks
        )
        clear_completed_btn.pack(side="left", padx=2)
        
        reset_failed_btn = ctk.CTkButton(
            queue_btn_frame,
            text="重置失败",
            width=80,
            height=30,
            command=self.reset_failed_tasks
        )
        reset_failed_btn.pack(side="left", padx=2)
        
        # 课程搜索添加
        search_frame = ctk.CTkFrame(right_frame)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(search_frame, text="添加课程:").pack(side="left", padx=(10, 5))
        
        self.course_search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="输入课程ID或名称搜索",
            width=200
        )
        self.course_search_entry.pack(side="left", padx=5)
        
        add_course_btn = ctk.CTkButton(
            search_frame,
            text="搜索添加",
            width=80,
            height=30,
            command=self.search_and_add_course
        )
        add_course_btn.pack(side="left", padx=5)
        
        # 抢课队列列表
        queue_list_frame = ctk.CTkFrame(right_frame)
        queue_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 创建队列Treeview
        queue_columns = ("优先级", "课程ID", "课程名称", "状态", "尝试次数")
        self.queue_tree = ttk.Treeview(queue_list_frame, columns=queue_columns, show="headings", height=12)
        
        # 设置列标题和宽度
        self.queue_tree.heading("优先级", text="优先级")
        self.queue_tree.heading("课程ID", text="课程ID")
        self.queue_tree.heading("课程名称", text="课程名称")
        self.queue_tree.heading("状态", text="状态")
        self.queue_tree.heading("尝试次数", text="尝试次数")
        
        self.queue_tree.column("优先级", width=60)
        self.queue_tree.column("课程ID", width=80)
        self.queue_tree.column("课程名称", width=200)
        self.queue_tree.column("状态", width=80)
        self.queue_tree.column("尝试次数", width=80)
        
        # 队列滚动条
        queue_scrollbar = ttk.Scrollbar(queue_list_frame, orient="vertical", command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=queue_scrollbar.set)
        
        # 打包队列相关组件
        self.queue_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        queue_scrollbar.pack(side="right", fill="y", pady=10, padx=(0, 10))
        
        # 绑定队列右键菜单
        self.queue_tree.bind("<Button-3>", self.show_queue_context_menu)
        
        # 日志区域
        log_frame = ctk.CTkFrame(self.scheduled_tab)
        log_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(log_frame, text="抢课日志:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5), anchor="w", padx=15)
        
        self.scheduled_log_textbox = ctk.CTkTextbox(log_frame, height=100)
        self.scheduled_log_textbox.pack(fill="x", padx=15, pady=(0, 15))
        
        # 设置调度器回调
        self.scheduler.set_callbacks(self.log_scheduled_message, self.update_scheduled_status)
        
        # 初始更新队列显示
        self.update_queue_display()
        
        # 启动时间更新
        self.update_current_time()
    
    def create_settings_tab(self):
        """创建设置选项卡"""
        # 标题
        title = ctk.CTkLabel(
            self.settings_tab,
            text="系统设置",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(20, 30))
        
        # 外观设置框架
        appearance_frame = ctk.CTkFrame(self.settings_tab)
        appearance_frame.pack(fill="x", padx=50, pady=20)
        
        ctk.CTkLabel(appearance_frame, text="外观设置", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        # 主题选择
        theme_frame = ctk.CTkFrame(appearance_frame)
        theme_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(theme_frame, text="主题:").pack(side="left", padx=(10, 20))
        
        self.theme_var = ctk.StringVar(value="dark")
        theme_option = ctk.CTkOptionMenu(
            theme_frame,
            values=["light", "dark", "system"],
            variable=self.theme_var,
            command=self.change_theme
        )
        theme_option.pack(side="left", padx=10)
        
        # 关于框架
        about_frame = ctk.CTkFrame(self.settings_tab)
        about_frame.pack(fill="x", padx=50, pady=20)
        
        ctk.CTkLabel(about_frame, text="关于", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        about_text = """NCC选课助手 v1.0 
作者：Cormac@CSE
        
基于Python重构的NCC选课系统助手
功能包括：课程查询、自动选课、定时选课等

⚠️ 使用说明：
1. 首先登录获取会话cookie
2. 获取课程列表查看可选课程
3. 使用自动选课功能进行抢课
4. 抢课系统请求限流，12小时内每人每个接口200次，超出后会抢课失败
5. 服务器会拒绝一秒内的重复请求提交，建议抢课间隔大于0.97秒（考虑到延迟）

开源项目，仅供学习交流使用，因为使用该软件导致的任何后果，作者不承担任何责任"""
        
        about_label = ctk.CTkLabel(
            about_frame,
            text=about_text,
            justify="left",
            font=ctk.CTkFont(size=12)
        )
        about_label.pack(pady=(0, 15), padx=20)
    
    def load_captcha(self):
        """加载验证码"""
        try:
            img_bytes, uuid = self.client.get_captcha()
            self.captcha_uuid = uuid
            
            # 转换为PIL图像
            img = Image.open(io.BytesIO(img_bytes))
            photo = ImageTk.PhotoImage(img)
            
            # 更新标签
            self.captcha_label.configure(image=photo, text="")
            self.captcha_label.image = photo  # 保持引用
            
        except Exception as e:
            messagebox.showerror("错误", f"获取验证码失败: {str(e)}")
    
    def login(self):
        """登录"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        code = self.captcha_entry.get().strip()
        
        if not all([username, password, code, self.captcha_uuid]):
            messagebox.showwarning("警告", "请填写完整的登录信息")
            return
        
        def login_thread():
            try:
                self.login_btn.configure(state="disabled", text="登录中...")
                token = self.client.login(username, password, code, self.captcha_uuid)
                
                # 获取用户信息
                user_info = self.client.get_user_info()
                self.user_info = user_info
                
                # 更新UI
                self.root.after(0, lambda: self.login_status.configure(
                    text="登录成功！", text_color="green"
                ))
                self.root.after(0, lambda: self.token_entry.delete(0, "end"))
                self.root.after(0, lambda: self.token_entry.insert(0, token))
                
                # 切换到用户信息界面
                self.root.after(0, self.update_user_info_display)
                self.root.after(0, self.show_user_info)
                
                messagebox.showinfo("成功", "登录成功！")
                
            except Exception as e:
                messagebox.showerror("错误", f"登录失败: {str(e)}")
                self.root.after(0, self.load_captcha)  # 重新加载验证码
            finally:
                self.root.after(0, lambda: self.login_btn.configure(state="normal", text="登录"))
        
        # 在新线程中执行登录
        threading.Thread(target=login_thread, daemon=True).start()
    
    def token_login(self):
        """使用Token登录"""
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showwarning("警告", "请输入Token")
            return
        
        def token_login_thread():
            try:
                self.client.set_token(token)
                # 验证Token有效性并获取用户信息
                user_info = self.client.get_user_info()
                self.user_info = user_info
                
                # 更新UI
                self.root.after(0, lambda: self.login_status.configure(text="Token登录成功！", text_color="green"))
                
                # 切换到用户信息界面
                self.root.after(0, self.update_user_info_display)
                self.root.after(0, self.show_user_info)
                
                messagebox.showinfo("成功", "Token登录成功！")
                
            except Exception as e:
                messagebox.showerror("错误", f"Token登录失败: {str(e)}")
        
        # 在新线程中执行Token登录
        threading.Thread(target=token_login_thread, daemon=True).start()
    
    def logout(self):
        """注销登录"""
        def logout_thread():
            try:
                self.client.logout()
                
                # 清除用户信息
                self.user_info = None
                
                # 切换回登录表单
                self.root.after(0, self.show_login_form)
                self.root.after(0, lambda: self.login_status.configure(text="已注销", text_color="orange"))
                
                # 清空表单
                self.root.after(0, lambda: self.username_entry.delete(0, "end"))
                self.root.after(0, lambda: self.password_entry.delete(0, "end"))
                self.root.after(0, lambda: self.captcha_entry.delete(0, "end"))
                self.root.after(0, lambda: self.token_entry.delete(0, "end"))
                
                # 重新加载验证码
                self.root.after(0, self.load_captcha)
                
                messagebox.showinfo("成功", "已成功注销")
                
            except Exception as e:
                messagebox.showerror("错误", f"注销失败: {str(e)}")
        
        # 在新线程中执行注销
        threading.Thread(target=logout_thread, daemon=True).start()
    
    def show_course_context_menu(self, event):
        """显示课程右键菜单"""
        if not self.courses_loaded:
            messagebox.showwarning("警告", "请先获取课程列表")
            return
        
        # 获取点击的项目
        item = self.course_tree.identify_row(event.y)
        if not item:
            return
        
        # 选择该项目
        self.course_tree.selection_set(item)
        
        # 获取课程信息
        values = self.course_tree.item(item)['values']
        course_id = values[0]
        
        # 找到对应的课程对象
        target_course = None
        for course in self.courses:
            if course.course_id == course_id:
                target_course = course
                break
        
        if not target_course:
            return
        
        # 创建右键菜单
        context_menu = tk.Menu(self.root, tearoff=0)
        
        # 检查是否已在队列中
        in_queue = self.course_queue.contains_course(course_id)
        
        if in_queue:
            context_menu.add_command(
                label="从抢课队列移除",
                command=lambda: self.remove_from_queue(target_course)
            )
            context_menu.add_command(
                label="调整优先级",
                command=lambda: self.adjust_priority(target_course)
            )
        else:
            context_menu.add_command(
                label="添加至抢课队列",
                command=lambda: self.add_to_queue(target_course)
            )
        
        context_menu.add_separator()
        context_menu.add_command(
            label="查看课程详情",
            command=lambda: self.show_course_detail(target_course)
        )
        
        # 显示菜单
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def add_to_queue(self, course: Course):
        """添加课程到抢课队列"""
        if not self.courses_loaded:
            messagebox.showwarning("警告", "请先获取课程列表")
            return
        
        # 弹出优先级设置对话框
        priority = self.get_priority_input()
        if priority is None:
            return
        
        success = self.course_queue.add_course(course, priority)
        if success:
            self.update_course_list()  # 更新背景色
            self.update_queue_display()
            messagebox.showinfo("成功", f"已添加 {course.course_name} 到抢课队列")
        else:
            messagebox.showwarning("警告", "该课程已在抢课队列中")
    
    def remove_from_queue(self, course: Course):
        """从抢课队列移除课程"""
        success = self.course_queue.remove_course(course.course_id)
        if success:
            self.update_course_list()  # 更新背景色
            self.update_queue_display()
            messagebox.showinfo("成功", f"已从抢课队列移除 {course.course_name}")
        else:
            messagebox.showwarning("警告", "该课程不在抢课队列中")
    
    def adjust_priority(self, course: Course):
        """调整课程优先级"""
        current_priority = None
        for task in self.course_queue.get_all_tasks():
            if task.course.course_id == course.course_id:
                current_priority = task.priority
                break
        
        if current_priority is None:
            messagebox.showwarning("警告", "该课程不在抢课队列中")
            return
        
        new_priority = self.get_priority_input(current_priority)
        if new_priority is None or new_priority == current_priority:
            return
        
        success = self.course_queue.update_priority(course.course_id, new_priority)
        if success:
            self.update_queue_display()
            messagebox.showinfo("成功", f"已更新 {course.course_name} 的优先级为 {new_priority}")
    
    def get_priority_input(self, current_priority=1):
        """获取优先级输入"""
        # 创建居中的输入对话框
        dialog = ctk.CTkInputDialog(
            text=f"请输入优先级 (数字越小优先级越高)\n当前优先级: {current_priority}",
            title="设置优先级"
        )
        
        # 居中对话框
        self.center_dialog(dialog)
        
        result = dialog.get_input()
        
        if result is None:
            return None
        
        try:
            priority = int(result)
            if priority < 1:
                messagebox.showwarning("警告", "优先级必须大于等于1")
                return None
            return priority
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的数字")
            return None
    
    def show_course_detail(self, course: Course):
        """显示课程详情"""
        detail_text = f"""课程详情:

课程ID: {course.course_id}
课程代码: {course.course_code}
课程名称: {course.course_name}
学期: {course.semester_name}
专业: {course.major}
学分: {course.credit}
学时: {course.credit_hour}
已选/可选: {course.selected}/{course.optional}
开课时间: {course.c_start_date} - {course.c_end_date}
状态: {course.status}
选择状态: {'已选' if course.chosen else '未选'}
可选择: {'是' if course.choosable else '否'}"""
        
        messagebox.showinfo("课程详情", detail_text)
    
    def get_courses(self):
        """获取课程列表"""
        if not self.client.is_logged_in():
            messagebox.showwarning("警告", "请先登录")
            return
        
        def get_courses_thread():
            try:
                courses = self.client.get_courses()
                self.courses = courses
                
                # 保存到文件
                self.client.save_courses_to_file(courses)
                
                # 更新UI
                self.root.after(0, self.update_course_list)
                self.root.after(0, lambda: self.course_info_label.configure(
                    text=f"共获取到 {len(courses)} 门课程"
                ))
                
                # 标记课程已加载并重建队列
                self.courses_loaded = True
                self.course_queue.rebuild_from_courses(courses)
                self.root.after(0, self.update_queue_display)
                
                messagebox.showinfo("成功", f"成功获取 {len(courses)} 门课程")
                
            except Exception as e:
                messagebox.showerror("错误", f"获取课程列表失败: {str(e)}")
        
        threading.Thread(target=get_courses_thread, daemon=True).start()
    
    def update_course_list(self):
        """更新课程列表显示"""
        # 清空现有数据
        for item in self.course_tree.get_children():
            self.course_tree.delete(item)
        
        # 添加新数据并设置背景色
        for course in self.courses:
            item_id = self.course_tree.insert("", "end", values=(
                course.course_id,
                course.course_code,
                course.course_name,
                course.semester_name,
                course.major,
                course.credit,
                f"{course.selected}/{course.optional}"
            ))
            
            # 如果课程在抢课队列中，设置背景色为绿色
            if self.course_queue.contains_course(course.course_id):
                # 使用tag设置背景色
                self.course_tree.item(item_id, tags=("in_queue",))
        
        # 配置tag样式
        self.course_tree.tag_configure("in_queue", background="lightgreen")
    
    def filter_courses(self, event=None):
        """过滤课程列表"""
        search_text = self.search_entry.get().lower()
        
        # 清空现有显示
        for item in self.course_tree.get_children():
            self.course_tree.delete(item)
        
        # 添加过滤后的数据
        for course in self.courses:
            if (search_text in course.course_name.lower() or 
                search_text in course.course_code.lower()):
                item_id = self.course_tree.insert("", "end", values=(
                    course.course_id,
                    course.course_code,
                    course.course_name,
                    course.semester_name,
                    course.major,
                    course.credit,
                    f"{course.selected}/{course.optional}"
                ))
                
                # 如果课程在抢课队列中，设置背景色为绿色
                if self.course_queue.contains_course(course.course_id):
                    self.course_tree.item(item_id, tags=("in_queue",))
        
        # 配置tag样式
        self.course_tree.tag_configure("in_queue", background="lightgreen")
    
    def refresh_courses(self):
        """刷新课程列表"""
        try:
            courses = self.client.load_courses_from_file()
            if courses:
                self.courses = courses
                self.update_course_list()
                self.course_info_label.configure(text=f"从本地加载了 {len(courses)} 门课程")
            else:
                self.course_info_label.configure(text="本地无课程数据，请先获取课程列表")
        except Exception as e:
            messagebox.showerror("错误", f"刷新失败: {str(e)}")
    
    def on_course_select(self, event):
        """课程选择事件"""
        selection = self.course_tree.selection()
        if selection:
            item = self.course_tree.item(selection[0])
            values = item['values']
            course_id = values[0]
            
            # 找到对应的课程对象
            for course in self.courses:
                if course.course_id == course_id:
                    self.selected_course = course
                    # 自动填充课程ID到自动选课页面
                    self.course_id_entry.delete(0, "end")
                    self.course_id_entry.insert(0, str(course_id))
                    break
    
    def start_auto_select(self):
        """开始自动选课"""
        if not self.client.is_logged_in():
            messagebox.showwarning("警告", "请先登录")
            return
        
        course_id_str = self.course_id_entry.get().strip()
        if not course_id_str:
            messagebox.showwarning("警告", "请输入课程ID")
            return
        
        try:
            course_id = int(course_id_str)
        except ValueError:
            messagebox.showwarning("警告", "课程ID必须是数字")
            return
        
        # 获取选课间隔
        interval_str = self.interval_entry.get().strip()
        if interval_str:
            try:
                Config.TIME_INTERVAL = float(interval_str)
            except ValueError:
                messagebox.showwarning("警告", "选课间隔必须是数字")
                return
        
        # 创建课程对象
        target_course = None
        for course in self.courses:
            if course.course_id == course_id:
                target_course = course
                break
        
        if not target_course:
            target_course = Course(
                course_id=course_id,
                course_code="",
                course_name=f"课程{course_id}",
                semester_name="",
                major="",
                optional=0,
                selected=0,
                c_start_date="",
                c_end_date="",
                status=0,
                credit="",
                credit_hour="",
                chosen=0,
                choosable=0
            )
        
        # 开始自动选课
        self.auto_select_running = True
        self.start_auto_btn.configure(state="disabled")
        self.stop_auto_btn.configure(state="normal")
        
        def auto_select_thread():
            def log_callback(message):
                timestamp = time.strftime("%H:%M:%S")
                log_message = f"[{timestamp}] {message}\n"
                self.root.after(0, lambda: self.log_textbox.insert("end", log_message))
                self.root.after(0, lambda: self.log_textbox.see("end"))
            
            def stop_flag():
                return not self.auto_select_running
            
            try:
                log_callback(f"开始自动选课: {target_course.course_name} (ID: {course_id})")
                log_callback(f"选课间隔: {Config.TIME_INTERVAL}秒")
                
                success = self.client.auto_select_course(target_course, log_callback, stop_flag)
                
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("成功", "选课成功！"))
                
            except Exception as e:
                error_msg = f"自动选课出错: {str(e)}"
                log_callback(error_msg)
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            finally:
                self.auto_select_running = False
                self.root.after(0, lambda: self.start_auto_btn.configure(state="normal"))
                self.root.after(0, lambda: self.stop_auto_btn.configure(state="disabled"))
        
        threading.Thread(target=auto_select_thread, daemon=True).start()
    
    def stop_auto_select(self):
        """停止自动选课"""
        if self.auto_select_running:
            self.auto_select_running = False
            
            timestamp = time.strftime("%H:%M:%S")
            self.log_textbox.insert("end", f"[{timestamp}] 正在停止自动选课...\n")
            self.log_textbox.see("end")
            
            # 立即更新按钮状态，让用户看到响应
            self.stop_auto_btn.configure(text="正在停止...", state="disabled")
            
            # 延迟恢复按钮状态，给停止操作时间
            def reset_buttons():
                self.start_auto_btn.configure(state="normal")
                self.stop_auto_btn.configure(text="停止自动选课", state="disabled")
            
            self.root.after(1000, reset_buttons)  # 1秒后恢复按钮状态
    
    def clear_log(self):
        """清空日志"""
        self.log_textbox.delete("1.0", "end")
    
    def change_theme(self, theme):
        """更改主题"""
        ctk.set_appearance_mode(theme)
    
    # 定时选课相关方法
    def search_and_add_course(self):
        """搜索并添加课程到队列"""
        if not self.courses_loaded:
            messagebox.showwarning("警告", "请先获取课程列表")
            return
        
        search_text = self.course_search_entry.get().strip()
        if not search_text:
            messagebox.showwarning("警告", "请输入搜索内容")
            return
        
        # 搜索课程
        found_courses = []
        search_lower = search_text.lower()
        
        for course in self.courses:
            if (search_lower in str(course.course_id) or
                search_lower in course.course_name.lower() or
                search_lower in course.course_code.lower()):
                found_courses.append(course)
        
        if not found_courses:
            messagebox.showwarning("警告", "未找到匹配的课程")
            return
        
        if len(found_courses) == 1:
            # 直接添加
            self.add_to_queue(found_courses[0])
        else:
            # 显示选择对话框
            self.show_course_selection_dialog(found_courses)
    
    def show_course_selection_dialog(self, courses):
        """显示课程选择对话框"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("选择课程")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 标题
        title_label = ctk.CTkLabel(dialog, text="找到多门课程，请选择:", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=10)
        
        # 课程列表
        list_frame = ctk.CTkFrame(dialog)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 创建listbox
        self.dialog_listbox = tk.Listbox(list_frame, font=("Arial", 10))
        
        for course in courses:
            self.dialog_listbox.insert("end", f"[{course.course_id}] {course.course_name} - {course.course_code}")
        
        self.dialog_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 按钮
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        def add_selected():
            selection = self.dialog_listbox.curselection()
            if selection:
                selected_course = courses[selection[0]]
                dialog.destroy()
                self.add_to_queue(selected_course)
            else:
                messagebox.showwarning("警告", "请选择一门课程")
        
        add_btn = ctk.CTkButton(btn_frame, text="添加到队列", command=add_selected)
        add_btn.pack(side="left", padx=5)
        
        cancel_btn = ctk.CTkButton(btn_frame, text="取消", command=dialog.destroy)
        cancel_btn.pack(side="right", padx=5)
    
    def update_queue_display(self):
        """更新抢课队列显示"""
        # 清空现有数据
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)
        
        # 获取所有任务并显示
        tasks = self.course_queue.get_all_tasks()
        
        for task in tasks:
            # 状态文本
            status_text = {
                "pending": "待抢课",
                "running": "抢课中",
                "success": "已成功",
                "failed": "已失败"
            }.get(task.status, task.status)
            
            item_id = self.queue_tree.insert("", "end", values=(
                task.priority,
                task.course.course_id,
                task.course.course_name,
                status_text,
                task.attempts
            ))
            
            # 根据状态设置颜色
            if task.status == "success":
                self.queue_tree.item(item_id, tags=("success",))
            elif task.status == "failed":
                self.queue_tree.item(item_id, tags=("failed",))
            elif task.status == "running":
                self.queue_tree.item(item_id, tags=("running",))
        
        # 配置tag样式
        self.queue_tree.tag_configure("success", background="lightgreen")
        self.queue_tree.tag_configure("failed", background="lightcoral")
        self.queue_tree.tag_configure("running", background="lightyellow")
        
        # 更新统计信息
        total_count = len(tasks)
        pending_count = len([t for t in tasks if t.status == "pending"])
        success_count = len([t for t in tasks if t.status == "success"])
        
        self.queue_count_label.configure(
            text=f"队列课程: {total_count} (待抢: {pending_count}, 成功: {success_count})"
        )
    
    def show_queue_context_menu(self, event):
        """显示队列右键菜单"""
        item = self.queue_tree.identify_row(event.y)
        if not item:
            return
        
        self.queue_tree.selection_set(item)
        values = self.queue_tree.item(item)['values']
        course_id = values[1]
        
        # 创建右键菜单
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(
            label="调整优先级",
            command=lambda: self.adjust_queue_priority(course_id)
        )
        context_menu.add_command(
            label="从队列移除",
            command=lambda: self.remove_from_queue_by_id(course_id)
        )
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def adjust_queue_priority(self, course_id):
        """调整队列中课程的优先级"""
        # 找到课程对象
        target_course = None
        for course in self.courses:
            if course.course_id == course_id:
                target_course = course
                break
        
        if target_course:
            self.adjust_priority(target_course)
    
    def remove_from_queue_by_id(self, course_id):
        """通过ID从队列移除课程"""
        # 找到课程对象
        target_course = None
        for course in self.courses:
            if course.course_id == course_id:
                target_course = course
                break
        
        if target_course:
            self.remove_from_queue(target_course)
    
    def clear_completed_tasks(self):
        """清除已完成的任务"""
        self.course_queue.clear_completed()
        self.update_queue_display()
        self.update_course_list()  # 更新背景色
        messagebox.showinfo("成功", "已清除已完成的任务")
    
    def reset_failed_tasks(self):
        """重置失败的任务"""
        self.course_queue.reset_failed_tasks()
        self.update_queue_display()
        messagebox.showinfo("成功", "已重置失败任务为待处理状态")
    
    def set_scheduled_grab(self):
        """设置定时抢课"""
        if not self.courses_loaded:
            messagebox.showwarning("警告", "请先获取课程列表")
            return
        
        if not self.client.is_logged_in():
            messagebox.showwarning("警告", "请先登录")
            return
        
        pending_tasks = self.course_queue.get_pending_tasks()
        if not pending_tasks:
            messagebox.showwarning("警告", "抢课队列为空，请先添加要抢的课程")
            return
        
        try:
            # 获取设置的时间
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            second = int(self.second_var.get())
            
            target_time = datetime(year, month, day, hour, minute, second)
            
            # 检查时间是否在未来
            if target_time <= datetime.now():
                messagebox.showwarning("警告", "计划时间必须在未来")
                return
            
            # 获取抢课间隔
            freq_text = self.freq_entry.get().strip()
            if freq_text:
                try:
                    grab_interval = float(freq_text)
                    if grab_interval < 0.1:
                        messagebox.showwarning("警告", "抢课间隔不能小于0.1秒")
                        return
                except ValueError:
                    messagebox.showwarning("警告", "请输入有效的抢课间隔")
                    return
            else:
                grab_interval = 1.0
            
            # 设置定时任务
            self.scheduler.schedule_grab(target_time, grab_interval)
            
            # 更新UI状态
            self.scheduled_time_label.configure(text=f"计划时间: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.scheduled_status_label.configure(text="状态: 已设置定时")
            self.schedule_btn.configure(state="disabled")
            self.stop_scheduled_btn.configure(state="normal", text="清除定时")
            
            messagebox.showinfo("成功", f"定时抢课已设置\n时间: {target_time.strftime('%Y-%m-%d %H:%M:%S')}\n队列中有 {len(pending_tasks)} 门课程")
            
        except ValueError as e:
            messagebox.showerror("错误", f"时间设置错误: {str(e)}")
    
    def start_immediate_grab(self):
        """立即开始抢课"""
        if not self.courses_loaded:
            messagebox.showwarning("警告", "请先获取课程列表")
            return
        
        if not self.client.is_logged_in():
            messagebox.showwarning("警告", "请先登录")
            return
        
        pending_tasks = self.course_queue.get_pending_tasks()
        if not pending_tasks:
            messagebox.showwarning("警告", "抢课队列为空，请先添加要抢的课程")
            return
        
        # 获取抢课间隔
        freq_text = self.freq_entry.get().strip()
        if freq_text:
            try:
                grab_interval = float(freq_text)
                if grab_interval < 0.1:
                    messagebox.showwarning("警告", "抢课间隔不能小于0.1秒")
                    return
                self.scheduler.grab_interval = grab_interval
            except ValueError:
                messagebox.showwarning("警告", "请输入有效的抢课间隔")
                return
        
        success = self.scheduler.start_immediate_grab()
        if success:
            self.start_now_btn.configure(state="disabled")
            self.stop_scheduled_btn.configure(state="normal", text="停止抢课")
            self.scheduled_status_label.configure(text="状态: 抢课中")
        else:
            messagebox.showwarning("警告", "抢课已在进行中")
    
    def stop_scheduled_grab(self):
        """停止定时抢课或清除定时设置"""
        if self.scheduler.is_running:
            # 如果正在抢课，停止抢课
            success = self.scheduler.stop_grab()
            if success:
                self.schedule_btn.configure(state="normal")
                self.start_now_btn.configure(state="normal")
                self.stop_scheduled_btn.configure(state="disabled", text="停止抢课")
                self.scheduled_status_label.configure(text="状态: 已停止")
            self.update_queue_display()
        else:
            # 如果没有在抢课，说明是设置了定时但还没开始，清除定时设置
            self.clear_scheduled_timer()
    
    def clear_scheduled_timer(self):
        """清除定时设置"""
        import schedule
        schedule.clear()  # 清除所有定时任务
        
        # 重置UI状态
        self.schedule_btn.configure(state="normal")
        self.start_now_btn.configure(state="normal")
        self.stop_scheduled_btn.configure(state="disabled", text="停止抢课")
        self.scheduled_status_label.configure(text="状态: 未设置")
        self.scheduled_time_label.configure(text="计划时间: 未设置")
        
        messagebox.showinfo("成功", "已清除定时设置")
    
    def log_scheduled_message(self, message):
        """记录定时抢课日志"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.root.after(0, lambda: self.scheduled_log_textbox.insert("end", log_message))
        self.root.after(0, lambda: self.scheduled_log_textbox.see("end"))
        self.root.after(0, self.update_queue_display)  # 更新队列显示
    
    def update_scheduled_status(self, status):
        """更新定时抢课状态"""
        self.root.after(0, lambda: self.scheduled_status_label.configure(text=f"状态: {status}"))
        
        if status in ["已停止", "已完成"]:
            self.root.after(0, lambda: self.schedule_btn.configure(state="normal"))
            self.root.after(0, lambda: self.start_now_btn.configure(state="normal"))
            self.root.after(0, lambda: self.stop_scheduled_btn.configure(state="disabled", text="停止抢课"))
    
    def update_current_time(self):
        """更新当前时间显示"""
        try:
            current_time = datetime.now()
            time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 添加北京时间标识
            time_display = f"当前时间: {time_str} (北京时间)"
            
            # 如果在定时选课选项卡中，更新时间显示
            if hasattr(self, 'current_time_label'):
                self.current_time_label.configure(text=time_display)
            
            # 每秒更新一次时间
            self.root.after(1000, self.update_current_time)
            
        except Exception:
            # 如果出错，仍然继续更新
            self.root.after(1000, self.update_current_time)
    
    def use_current_time(self):
        """使用当前时间设置定时"""
        now = datetime.now()
        
        # 设置为当前时间
        self.year_var.set(str(now.year))
        self.month_var.set(str(now.month))
        self.day_var.set(str(now.day))
        self.hour_var.set(f"{now.hour:02d}")
        self.minute_var.set(f"{now.minute:02d}")
        self.second_var.set(f"{now.second:02d}")
        
        messagebox.showinfo("提示", f"已设置为当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    

    def on_closing(self):
        """窗口关闭事件"""
        # 检查是否有正在运行的任务
        should_close = True
        
        if self.auto_select_running:
            should_close = messagebox.askokcancel("退出", "自动选课正在运行，确定要退出吗？")
            if should_close:
                self.auto_select_running = False
        
        if self.scheduler.is_running:
            should_close = messagebox.askokcancel("退出", "定时抢课正在运行，确定要退出吗？")
            if should_close:
                self.scheduler.stop_grab()
        
        if should_close:
            self.client.close()
            self.root.destroy()
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()


def main():
    """主函数"""
    app = CourseSelectionGUI()
    app.run()


if __name__ == "__main__":
    main()
