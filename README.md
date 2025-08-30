# HUST-NCC-Course-Fucker

Inspired by [HUST-OCSS-Fucker](https://github.com/7erryX/HUST-OCSS-Fucker) - Go CLI version

基于Python重构的HUST-NCC选课系统助手，带GUI。

## 功能特点

-  **GUI界面** - 基于CustomTkinter
-  **两种登录** - 支持验证码登录和Token快速登录
-  **课程列表** - 获取、查看、搜索可选课程
-  **自动选课** - 智能抢课，支持自定义间隔
-  **定时抢课** - 支持多个课程同时抢，设置好时间就行

## 安装要求

- Python 3.7+
- 依赖包见 `requirements.txt`

## 快速开始

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **运行程序**
   ```bash
   python main.py
   ```

## 使用说明

### 1. 登录
- **普通登录**: 输入学号、密码和验证码
- **Token登录**: 使用cookie中的Admin-Token字段作为token登录

### 2. 获取课程列表
- 登录成功后，点击"获取课程列表"
- 支持课程搜索和筛选
- 课程信息自动保存到本地

### 3. 自动选课
- 选择目标课程或输入课程ID
- 设置选课间隔（建议0.97秒以上）
- 点击"开始自动选课"进行抢课

### 4.

## 项目结构

```
├── main.py          # 主程序入口
├── gui.py           # GUI界面
├── client.py        # 主客户端类
├── auth.py          # 认证模块
├── course.py        # 课程管理模块
├── config.py        # 配置文件
├── schedular.py     # 定时抢课调度模块
├── requirements.txt # 依赖包
└── README.md        # 说明文档
```

## 配置说明

### 主要配置项 (config.py)

- `BASE_URL`: ncc选课系统地址
- `TIME_INTERVAL`: 选课间隔（秒）
- `REQUEST_TIMEOUT`: 请求超时时间
- `WINDOW_WIDTH/HEIGHT`: 窗口尺寸

### 文件配置

- `course_list.yaml`: 课程列表缓存
- `course_queue': 定时抢课队列

## 功能对比

| 功能 | Go版本 | Python版本 |
|------|--------|------------|
| 基础选课 | ✅ | ✅ |
| 课程管理 | ✅ | ✅ |
| GUI界面 | ❌ | ✅ |
| 账密登录 | ❌ | ✅ |
| 定时抢课 | ❌ | ✅ |
| 同时抢多个课 | ❌ | ✅ |
| 配置管理 | ✅ | ✅ |

## 注意事项

⚠️ **重要提醒**:
1. 请遵守学校选课规定，合理使用工具
2. 建议选课间隔设置在1秒以上，避免过于频繁的请求
3. 本工具仅供学习交流，作者不承担任何由本程序引发的责任
4. 使用前请确保网络环境稳定

## 开发相关

### 环境要求
- Python 3.7+
- customtkinter 5.2.2+
- requests 2.31.0+
- Pillow 10.0.1+
- PyYAML 6.0.1+

## 致谢

- 感谢7erryX哥[[Github主页](https://github.com/7erryX)]提供的开源go项目

## 许可证

本项目仅供学习交流使用，请遵守相关法律法规。