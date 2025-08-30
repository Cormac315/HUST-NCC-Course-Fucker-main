"""
配置文件
"""

class Config:
    # API 基础URL
    BASE_URL = "http://222.20.126.201"
    
    # API端点
    CAPTCHA_URL = f"{BASE_URL}/dev-api/captchaImage"
    LOGIN_URL = f"{BASE_URL}/dev-api/login"
    LOGOUT_URL = f"{BASE_URL}/dev-api/logout"
    PROFILE_URL = f"{BASE_URL}/dev-api/system/user/profile"
    USER_INFO_URL = f"{BASE_URL}/dev-api/getInfo"
    COURSES_URL = f"{BASE_URL}/dev-api/xuanke/course/student/"
    CLASS_URL = f"{BASE_URL}/dev-api/xuanke/class"
    SELECT_URL = f"{BASE_URL}/dev-api/xuanke/course"
    
    # 默认配置
    DEFAULT_TOKEN = ""
    DEFAULT_COURSE_ID = -1
    TIME_INTERVAL = 0.97  # 选课间隔（秒）
    
    # 文件配置
    COURSE_LIST_FILE = "course_list.yaml"
    CONFIG_FILE = "user_config.yaml"
    
    # 请求超时时间
    REQUEST_TIMEOUT = 10
    
    # GUI配置
    WINDOW_WIDTH = 1120
    WINDOW_HEIGHT = 955
