#!/usr/bin/env python3
"""
华科选课助手命令行版本
"""

import sys
import time
import argparse
from typing import List
from client import HUSTCourseClient
from course import Course
from config import Config
from utils import Logger


def get_input(prompt: str, required: bool = True) -> str:
    """获取用户输入"""
    while True:
        value = input(prompt).strip()
        if value or not required:
            return value
        print("这是必填项，请重新输入。")


def print_courses(courses: List[Course]):
    """打印课程列表"""
    if not courses:
        print("没有找到课程。")
        return
    
    print(f"\\n共找到 {len(courses)} 门课程:")
    print("-" * 100)
    print(f"{'ID':<8} {'代码':<12} {'课程名称':<30} {'学分':<6} {'已选/可选':<10}")
    print("-" * 100)
    
    for course in courses:
        print(f"{course.course_id:<8} {course.course_code:<12} {course.course_name[:28]:<30} {course.credit:<6} {course.selected}/{course.optional:<10}")


def login_flow(client: HUSTCourseClient) -> bool:
    """登录流程"""
    print("\\n=== 登录华科选课系统 ===")
    
    # 询问登录方式
    print("\\n请选择登录方式:")
    print("1. 用户名密码登录")
    print("2. Token登录")
    
    choice = get_input("请输入选择 (1/2): ")
    
    if choice == "2":
        # Token登录
        token = get_input("请输入Token: ")
        try:
            client.set_token(token)
            client.get_profile()  # 验证Token
            print("Token登录成功！")
            return True
        except Exception as e:
            print(f"Token登录失败: {e}")
            return False
    
    else:
        # 用户名密码登录
        username = get_input("学号: ")
        password = get_input("密码: ")
        
        try:
            # 获取验证码
            print("\\n正在获取验证码...")
            img_bytes, uuid = client.get_captcha()
            
            # 保存验证码图片
            with open("captcha.png", "wb") as f:
                f.write(img_bytes)
            print("验证码已保存为 captcha.png，请查看后输入。")
            
            code = get_input("验证码: ")
            
            # 登录
            token = client.login(username, password, code, uuid)
            print(f"\\n登录成功！")
            print(f"Token: {token}")
            return True
            
        except Exception as e:
            print(f"登录失败: {e}")
            return False


def get_courses_flow(client: HUSTCourseClient) -> List[Course]:
    """获取课程流程"""
    print("\\n=== 获取课程列表 ===")
    
    try:
        print("正在获取课程列表...")
        courses = client.get_courses()
        
        # 保存到文件
        client.save_courses_to_file(courses)
        print(f"课程列表已保存到 {Config.COURSE_LIST_FILE}")
        
        return courses
        
    except Exception as e:
        print(f"获取课程列表失败: {e}")
        return []


def select_course_flow(client: HUSTCourseClient, courses: List[Course]):
    """选课流程"""
    print("\\n=== 选择课程 ===")
    
    # 显示可选方式
    print("\\n请选择操作:")
    print("1. 从列表选择课程")
    print("2. 直接输入课程ID")
    
    choice = get_input("请输入选择 (1/2): ")
    
    target_course = None
    
    if choice == "1":
        if not courses:
            print("没有可用的课程列表，请先获取课程。")
            return
        
        # 显示课程列表
        print_courses(courses)
        
        while True:
            try:
                course_id = int(get_input("\\n请输入要选择的课程ID: "))
                for course in courses:
                    if course.course_id == course_id:
                        target_course = course
                        break
                
                if target_course:
                    break
                else:
                    print("未找到对应的课程，请重新输入。")
            except ValueError:
                print("请输入有效的数字。")
    
    else:
        # 直接输入课程ID
        while True:
            try:
                course_id = int(get_input("请输入课程ID: "))
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
                break
            except ValueError:
                print("请输入有效的数字。")
    
    if not target_course:
        print("未选择有效的课程。")
        return
    
    print(f"\\n选择的课程: {target_course.course_name} (ID: {target_course.course_id})")
    
    # 询问选课方式
    print("\\n请选择选课方式:")
    print("1. 单次选课")
    print("2. 自动选课 (持续尝试)")
    
    mode = get_input("请输入选择 (1/2): ")
    
    if mode == "1":
        # 单次选课
        try:
            print("\\n正在选课...")
            success = client.select_course(target_course)
            if success:
                print("选课成功！")
            else:
                print("选课失败。")
        except Exception as e:
            print(f"选课失败: {e}")
    
    else:
        # 自动选课
        interval_str = get_input(f"请输入选课间隔秒数 (默认 {Config.TIME_INTERVAL}): ", required=False)
        if interval_str:
            try:
                Config.TIME_INTERVAL = float(interval_str)
            except ValueError:
                print("间隔时间无效，使用默认值。")
        
        print(f"\\n开始自动选课...")
        print(f"目标课程: {target_course.course_name} (ID: {target_course.course_id})")
        print(f"选课间隔: {Config.TIME_INTERVAL}秒")
        print("按 Ctrl+C 停止\\n")
        
        attempt_count = 0
        
        try:
            while True:
                attempt_count += 1
                start_time = time.time()
                
                try:
                    success = client.select_course(target_course)
                    if success:
                        print(f"\\n选课成功！尝试次数: {attempt_count}")
                        break
                except Exception as e:
                    end_time = time.time()
                    elapsed = end_time - start_time
                    print(f"第{attempt_count}次尝试失败: {e}, 耗时: {elapsed:.3f}s")
                
                time.sleep(Config.TIME_INTERVAL)
                
        except KeyboardInterrupt:
            print(f"\\n用户停止了自动选课。总尝试次数: {attempt_count}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="华科选课助手命令行版本")
    parser.add_argument("--gui", action="store_true", help="启动GUI版本")
    parser.add_argument("--get-courses", action="store_true", help="获取课程列表")
    parser.add_argument("--course-id", type=int, help="直接指定课程ID进行选课")
    parser.add_argument("--token", type=str, help="使用指定Token登录")
    parser.add_argument("--interval", type=float, help="设置选课间隔", default=Config.TIME_INTERVAL)
    
    args = parser.parse_args()
    
    # 如果指定了GUI参数，启动GUI版本
    if args.gui:
        from gui import main as gui_main
        gui_main()
        return
    
    print("华科选课助手 - 命令行版本")
    print("=" * 50)
    
    # 初始化客户端
    client = HUSTCourseClient()
    courses = []
    
    try:
        # 设置间隔
        Config.TIME_INTERVAL = args.interval
        
        # 登录
        if args.token:
            client.set_token(args.token)
            try:
                client.get_profile()
                print("Token登录成功！")
            except Exception as e:
                print(f"Token登录失败: {e}")
                return
        else:
            if not login_flow(client):
                return
        
        # 获取课程列表
        if args.get_courses or args.course_id is None:
            courses = get_courses_flow(client)
            if courses:
                print_courses(courses)
        
        # 如果指定了课程ID，直接选课
        if args.course_id:
            target_course = Course(
                course_id=args.course_id,
                course_code="",
                course_name=f"课程{args.course_id}",
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
            
            print(f"\\n开始自动选课: 课程ID {args.course_id}")
            attempt_count = 0
            stop_requested = False
            
            def stop_flag():
                return stop_requested
            
            def log_callback(message):
                print(message)
            
            try:
                success = client.auto_select_course(target_course, log_callback, stop_flag)
                    
            except KeyboardInterrupt:
                print(f"\\n用户停止了自动选课。总尝试次数: {attempt_count}")
            
            return
        
        # 交互式流程
        while True:
            print("\\n=== 主菜单 ===")
            print("1. 获取课程列表")
            print("2. 选择课程")
            print("3. 退出")
            
            choice = get_input("请输入选择 (1-3): ")
            
            if choice == "1":
                courses = get_courses_flow(client)
                if courses:
                    print_courses(courses)
            
            elif choice == "2":
                select_course_flow(client, courses)
            
            elif choice == "3":
                print("感谢使用！")
                break
            
            else:
                print("无效的选择，请重新输入。")
    
    finally:
        client.close()


if __name__ == "__main__":
    main()
