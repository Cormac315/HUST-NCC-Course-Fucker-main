"""
主客户端类，整合所有功能
"""

import requests
import time
import yaml
from typing import List, Optional
from auth import AuthManager
from course import CourseManager, Course
from config import Config


class HUSTCourseClient:
    """华中科技大学选课客户端"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        self.auth_manager = AuthManager(self.session)
        self.course_manager = CourseManager(self.session)
    
    def get_captcha(self):
        """获取验证码"""
        return self.auth_manager.get_captcha()
    
    def login(self, username: str, password: str, code: str, uuid: str) -> str:
        """登录"""
        return self.auth_manager.login(username, password, code, uuid)
    
    def set_token(self, token: str):
        """设置令牌"""
        self.auth_manager.set_token(token)
    
    def is_logged_in(self) -> bool:
        """检查登录状态"""
        return self.auth_manager.is_logged_in()
    
    def get_profile(self) -> dict:
        """获取用户信息"""
        return self.auth_manager.get_profile()
    
    def get_user_info(self) -> dict:
        """获取详细用户信息"""
        return self.auth_manager.get_user_info()
    
    def logout(self) -> bool:
        """注销登录"""
        return self.auth_manager.logout()
    
    def get_courses(self) -> List[Course]:
        """获取课程列表"""
        return self.course_manager.get_courses()
    
    def save_courses_to_file(self, courses: List[Course], filename: str = None):
        """保存课程列表到文件"""
        if filename is None:
            filename = Config.COURSE_LIST_FILE
        
        course_data = []
        for course in courses:
            course_data.append({
                'course_id': course.course_id,
                'course_code': course.course_code,
                'course_name': course.course_name,
                'semester_name': course.semester_name,
                'major': course.major,
                'optional': course.optional,
                'selected': course.selected,
                'c_start_date': course.c_start_date,
                'c_end_date': course.c_end_date,
                'status': course.status,
                'credit': course.credit,
                'credit_hour': course.credit_hour,
                'chosen': course.chosen,
                'choosable': course.choosable
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(course_data, f, default_flow_style=False, allow_unicode=True)
    
    def load_courses_from_file(self, filename: str = None) -> List[Course]:
        """从文件加载课程列表"""
        if filename is None:
            filename = Config.COURSE_LIST_FILE
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                course_data = yaml.safe_load(f)
            
            courses = []
            for data in course_data:
                course = Course(
                    course_id=data.get('course_id'),
                    course_code=data.get('course_code', ''),
                    course_name=data.get('course_name', ''),
                    semester_name=data.get('semester_name', ''),
                    major=data.get('major', ''),
                    optional=data.get('optional', 0),
                    selected=data.get('selected', 0),
                    c_start_date=data.get('c_start_date', ''),
                    c_end_date=data.get('c_end_date', ''),
                    status=data.get('status', 0),
                    credit=data.get('credit', ''),
                    credit_hour=data.get('credit_hour', ''),
                    chosen=data.get('chosen', 0),
                    choosable=data.get('choosable', 0)
                )
                courses.append(course)
            
            return courses
        except FileNotFoundError:
            return []
    
    def select_course(self, course: Course) -> bool:
        """选择课程"""
        return self.course_manager.select_course(course)
    
    def auto_select_course(self, course: Course, callback=None, stop_flag=None) -> bool:
        """自动选课（持续尝试）"""
        success = False
        attempt_count = 0
        
        while not success:
            # 检查停止标志
            if stop_flag and stop_flag():
                if callback:
                    callback("用户停止了自动选课")
                return False
            
            attempt_count += 1
            start_time = time.time()
            
            try:
                success = self.select_course(course)
                if success:
                    if callback:
                        callback(f"选课成功！尝试次数: {attempt_count}")
                    break
            except Exception as e:
                end_time = time.time()
                elapsed = end_time - start_time
                
                if callback:
                    callback(f"第{attempt_count}次尝试失败: {str(e)}, 耗时: {elapsed:.3f}s")
                
                # 检查停止标志
                if stop_flag and stop_flag():
                    if callback:
                        callback("用户停止了自动选课")
                    return False
                
                # 短暂延迟后重试
                time.sleep(Config.TIME_INTERVAL)
        
        return success
    
    def get_time_diff(self) -> float:
        """获取客户端与服务器的时间差"""
        try:
            client_time = time.time()
            response = self.session.get(f"{Config.BASE_URL}/student/index", timeout=Config.REQUEST_TIMEOUT)
            
            if 'Date' in response.headers:
                server_time_str = response.headers['Date']
                server_time = time.mktime(time.strptime(server_time_str, '%a, %d %b %Y %H:%M:%S %Z'))
                return client_time - server_time
            else:
                raise Exception("无法获取服务器时间")
                
        except Exception as e:
            raise Exception(f"获取时间差失败: {str(e)}")
    
    def close(self):
        """关闭会话"""
        self.session.close()
