"""
定时选课调度器和抢课队列管理
"""

import time
import threading
import schedule
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from course import Course
from config import Config
import json


@dataclass
class CourseTask:
    """抢课任务"""
    course: Course
    priority: int = 1  # 优先级，数字越小优先级越高
    added_time: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, running, success, failed
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'course_id': self.course.course_id,
            'course_name': self.course.course_name,
            'course_code': self.course.course_code,
            'priority': self.priority,
            'added_time': self.added_time.isoformat(),
            'status': self.status,
            'attempts': self.attempts,
            'last_attempt': self.last_attempt.isoformat() if self.last_attempt else None
        }
    
    @classmethod
    def from_dict(cls, data: dict, course: Course) -> 'CourseTask':
        """从字典创建"""
        task = cls(
            course=course,
            priority=data.get('priority', 1),
            status=data.get('status', 'pending'),
            attempts=data.get('attempts', 0)
        )
        
        if data.get('added_time'):
            task.added_time = datetime.fromisoformat(data['added_time'])
        
        if data.get('last_attempt'):
            task.last_attempt = datetime.fromisoformat(data['last_attempt'])
        
        return task


class CourseQueue:
    """抢课队列管理器"""
    
    def __init__(self):
        self.tasks: List[CourseTask] = []
        self.lock = threading.Lock()
        self.save_file = "course_queue.json"
        self.load_queue()
    
    def add_course(self, course: Course, priority: int = 1) -> bool:
        """添加课程到队列"""
        with self.lock:
            # 检查是否已存在
            for task in self.tasks:
                if task.course.course_id == course.course_id:
                    return False
            
            task = CourseTask(course=course, priority=priority)
            self.tasks.append(task)
            self.sort_by_priority()
            self.save_queue()
            return True
    
    def remove_course(self, course_id: int) -> bool:
        """从队列移除课程"""
        with self.lock:
            for i, task in enumerate(self.tasks):
                if task.course.course_id == course_id:
                    self.tasks.pop(i)
                    self.save_queue()
                    return True
            return False
    
    def update_priority(self, course_id: int, priority: int) -> bool:
        """更新课程优先级"""
        with self.lock:
            for task in self.tasks:
                if task.course.course_id == course_id:
                    task.priority = priority
                    self.sort_by_priority()
                    self.save_queue()
                    return True
            return False
    
    def sort_by_priority(self):
        """按优先级排序"""
        self.tasks.sort(key=lambda x: (x.priority, x.added_time))
    
    def get_pending_tasks(self) -> List[CourseTask]:
        """获取待处理的任务"""
        with self.lock:
            return [task for task in self.tasks if task.status == "pending"]
    
    def get_all_tasks(self) -> List[CourseTask]:
        """获取所有任务"""
        with self.lock:
            return self.tasks.copy()
    
    def update_task_status(self, course_id: int, status: str, attempt_increment: bool = True):
        """更新任务状态"""
        with self.lock:
            for task in self.tasks:
                if task.course.course_id == course_id:
                    task.status = status
                    task.last_attempt = datetime.now()
                    if attempt_increment:
                        task.attempts += 1
                    self.save_queue()
                    break
    
    def clear_completed(self):
        """清除已完成的任务"""
        with self.lock:
            self.tasks = [task for task in self.tasks if task.status not in ["success"]]
            self.save_queue()
    
    def reset_failed_tasks(self):
        """重置失败的任务为待处理状态"""
        with self.lock:
            for task in self.tasks:
                if task.status == "failed":
                    task.status = "pending"
            self.save_queue()
    
    def save_queue(self):
        """保存队列到文件"""
        try:
            data = {
                'tasks': [task.to_dict() for task in self.tasks],
                'saved_time': datetime.now().isoformat()
            }
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存队列失败: {e}")
    
    def load_queue(self):
        """从文件加载队列"""
        try:
            with open(self.save_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 注意：这里需要配合课程数据来重建Course对象
            # 实际使用时需要传入课程列表
            self.tasks = []  # 先清空，等GUI加载时重新构建
            
        except FileNotFoundError:
            self.tasks = []
        except Exception as e:
            print(f"加载队列失败: {e}")
            self.tasks = []
    
    def rebuild_from_courses(self, courses: List[Course]):
        """从课程列表重建队列"""
        try:
            with open(self.save_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            course_dict = {course.course_id: course for course in courses}
            new_tasks = []
            
            for task_data in data.get('tasks', []):
                course_id = task_data.get('course_id')
                if course_id in course_dict:
                    task = CourseTask.from_dict(task_data, course_dict[course_id])
                    new_tasks.append(task)
            
            with self.lock:
                self.tasks = new_tasks
                self.sort_by_priority()
                
        except FileNotFoundError:
            # 文件不存在，这是正常的，不需要报错
            with self.lock:
                self.tasks = []
        except Exception as e:
            print(f"重建队列失败: {e}")
            with self.lock:
                self.tasks = []
    
    def contains_course(self, course_id: int) -> bool:
        """检查队列是否包含指定课程"""
        with self.lock:
            return any(task.course.course_id == course_id for task in self.tasks)


class ScheduledCourseGrabber:
    """定时抢课调度器"""
    
    def __init__(self, client, course_queue: CourseQueue):
        self.client = client
        self.course_queue = course_queue
        self.is_running = False
        self.scheduler_thread = None
        self.grab_thread = None
        self.stop_event = threading.Event()
        
        # 抢课配置
        self.grab_interval = 1.0  # 抢课间隔（秒）
        self.scheduled_time = None  # 计划开始时间
        self.auto_start = False  # 是否自动开始
        
        # 回调函数
        self.log_callback: Optional[Callable[[str], None]] = None
        self.status_callback: Optional[Callable[[str], None]] = None
    
    def set_callbacks(self, log_callback: Callable[[str], None], status_callback: Callable[[str], None]):
        """设置回调函数"""
        self.log_callback = log_callback
        self.status_callback = status_callback
    
    def schedule_grab(self, target_time: datetime, grab_interval: float = 1.0):
        """设置定时抢课"""
        self.scheduled_time = target_time
        self.grab_interval = grab_interval
        
        # 清除现有调度
        schedule.clear()
        
        # 设置定时任务
        beijing_tz = timezone(timedelta(hours=8))
        target_time_beijing = target_time.replace(tzinfo=beijing_tz)
        
        # 使用schedule库设置定时任务
        target_time_str = target_time.strftime("%H:%M")
        schedule.every().day.at(target_time_str).do(self._start_grabbing)
        
        self._log(f"已设置定时抢课: {target_time_beijing.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
        
        # 启动调度器线程
        if not self.scheduler_thread or not self.scheduler_thread.is_alive():
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
    
    def start_immediate_grab(self):
        """立即开始抢课"""
        if self.is_running:
            self._log("抢课已在进行中")
            return False
        
        self._start_grabbing()
        return True
    
    def stop_grab(self):
        """停止抢课"""
        if not self.is_running:
            return False
        
        self.stop_event.set()
        self.is_running = False
        
        if self.grab_thread and self.grab_thread.is_alive():
            self.grab_thread.join(timeout=5)
        
        self._log("抢课已停止")
        self._status("已停止")
        return True
    
    def _scheduler_loop(self):
        """调度器循环"""
        while True:
            try:
                schedule.run_pending()
                if self.stop_event.wait(1):  # 每秒检查一次
                    break
            except Exception as e:
                self._log(f"调度器错误: {e}")
    
    def _start_grabbing(self):
        """开始抢课"""
        if self.is_running:
            self._log("抢课已在进行中，跳过此次调度")
            return
        
        pending_tasks = self.course_queue.get_pending_tasks()
        if not pending_tasks:
            self._log("抢课队列为空，无需抢课")
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        self._log(f"开始抢课，队列中有 {len(pending_tasks)} 门课程")
        self._status("抢课中")
        
        # 启动抢课线程
        self.grab_thread = threading.Thread(target=self._grab_loop, daemon=True)
        self.grab_thread.start()
    
    def _grab_loop(self):
        """抢课循环"""
        try:
            round_count = 0
            
            while self.is_running and not self.stop_event.is_set():
                round_count += 1
                pending_tasks = self.course_queue.get_pending_tasks()
                
                if not pending_tasks:
                    self._log("所有课程抢课完成！")
                    break
                
                self._log(f"第 {round_count} 轮抢课开始，待抢课程: {len(pending_tasks)}")
                
                for task in pending_tasks:
                    if self.stop_event.is_set():
                        break
                    
                    # 更新任务状态为运行中
                    self.course_queue.update_task_status(task.course.course_id, "running")
                    
                    try:
                        self._log(f"正在抢课: {task.course.course_name} (ID: {task.course.course_id}) [优先级: {task.priority}]")
                        
                        success = self.client.select_course(task.course)
                        
                        if success:
                            self.course_queue.update_task_status(task.course.course_id, "success")
                            self._log(f"✅ 抢课成功: {task.course.course_name}")
                        else:
                            self.course_queue.update_task_status(task.course.course_id, "pending")
                            self._log(f"❌ 抢课失败: {task.course.course_name}")
                    
                    except Exception as e:
                        self.course_queue.update_task_status(task.course.course_id, "pending")
                        self._log(f"❌ 抢课出错: {task.course.course_name} - {str(e)}")
                    
                    # 等待间隔
                    if not self.stop_event.wait(self.grab_interval):
                        continue
                    else:
                        break
                
                # 检查是否还有待处理的任务
                remaining_pending = self.course_queue.get_pending_tasks()
                if not remaining_pending:
                    self._log("🎉 所有课程抢课成功！")
                    break
                
                self._log(f"第 {round_count} 轮完成，等待下一轮...")
                
                # 轮次间隔（稍长一些）
                if self.stop_event.wait(self.grab_interval * 2):
                    break
        
        except Exception as e:
            self._log(f"抢课循环出错: {e}")
        
        finally:
            self.is_running = False
            self._status("已停止")
            self._log("抢课任务结束")
    
    def _log(self, message: str):
        """日志输出"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)
    
    def _status(self, status: str):
        """状态更新"""
        if self.status_callback:
            self.status_callback(status)
    
    def get_status(self) -> dict:
        """获取当前状态"""
        pending_tasks = self.course_queue.get_pending_tasks()
        all_tasks = self.course_queue.get_all_tasks()
        
        return {
            'is_running': self.is_running,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'total_tasks': len(all_tasks),
            'pending_tasks': len(pending_tasks),
            'completed_tasks': len([t for t in all_tasks if t.status == "success"]),
            'failed_tasks': len([t for t in all_tasks if t.status == "failed"]),
            'grab_interval': self.grab_interval
        }
