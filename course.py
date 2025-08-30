"""
课程相关功能模块
"""

import json
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from config import Config


@dataclass
class Course:
    """课程数据类"""
    course_id: int
    course_code: str
    course_name: str
    semester_name: str
    major: str
    optional: int
    selected: int
    c_start_date: str
    c_end_date: str
    status: int
    credit: str
    credit_hour: str
    chosen: int
    choosable: int
    course_class_number: str = ""
    
    def __str__(self):
        return f"[{self.course_id}] {self.course_name} - {self.course_code}"


class CourseManager:
    """课程管理器"""
    
    def __init__(self, session: requests.Session):
        self.session = session
    
    def get_courses(self) -> List[Course]:
        """获取可选课程列表"""
        url = Config.COURSES_URL
        params = {
            "activeSemester": "true",
            "chosen": "false", 
            "choosable": "true",
            "pageNum": 1,
            "pageSize": 100
        }
        
        try:
            response = self.session.get(url, params=params, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") != 200:
                raise Exception(f"获取课程列表失败: {data.get('msg', '未知错误')}")
            
            courses = []
            for course_data in data.get("rows", []):
                course = Course(
                    course_id=course_data.get("courseId"),
                    course_code=course_data.get("courseCode", ""),
                    course_name=course_data.get("courseName", ""),
                    semester_name=course_data.get("semesterName", ""),
                    major=course_data.get("major", ""),
                    optional=course_data.get("optional", 0),
                    selected=course_data.get("selected", 0),
                    c_start_date=course_data.get("cStartDate", ""),
                    c_end_date=course_data.get("cEndDate", ""),
                    status=course_data.get("status", 0),
                    credit=course_data.get("credit", ""),
                    credit_hour=course_data.get("creditHour", ""),
                    chosen=course_data.get("chosen", 0),
                    choosable=course_data.get("choosable", 0)
                )
                courses.append(course)
            
            return courses
            
        except requests.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("响应数据格式错误")
    
    def get_course_class_number(self, course: Course) -> str:
        """获取课程班级编号"""
        url = f"{Config.CLASS_URL}/{course.course_id}/student"
        
        try:
            response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") != 200:
                raise Exception(f"获取班级信息失败: {data.get('msg', '未知错误')}")
            
            rows = data.get("rows", [])
            if not rows:
                raise Exception("没有可选择的课堂")
            
            class_number = rows[0].get("classNumber", "")
            if not class_number:
                raise Exception("课堂编号为空")
                
            course.course_class_number = class_number
            return class_number
            
        except requests.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("响应数据格式错误")
    
    def select_course(self, course: Course) -> bool:
        """选课"""
        if course.course_id <= 0:
            raise Exception("课程ID无效")
        
        if not course.course_class_number:
            self.get_course_class_number(course)
        
        url = f"{Config.SELECT_URL}/{course.course_id}/select"
        params = {"classNumber": course.course_class_number}
        
        try:
            response = self.session.put(url, params=params, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") != 200:
                msg = data.get("msg", "未知错误")
                if msg == "选课人数已达上限！":
                    raise Exception("选课人数已达上限")
                elif msg == "不在选课时段范围内！":
                    raise Exception("不在选课时段范围内")
                else:
                    raise Exception(f"选课失败: {msg}")
            
            return True
            
        except requests.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("响应数据格式错误")
