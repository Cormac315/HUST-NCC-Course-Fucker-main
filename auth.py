"""
认证相关功能模块
"""

import json
import base64
import requests
from typing import Tuple, Optional
from config import Config


class AuthManager:
    """认证管理器"""
    
    def __init__(self, session: requests.Session):
        self.session = session
        self.token: Optional[str] = None
    
    def get_captcha(self) -> Tuple[bytes, str]:
        """获取验证码图片和UUID"""
        try:
            response = self.session.get(Config.CAPTCHA_URL, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") != 200:
                raise Exception(f"获取验证码失败: {data.get('msg', '未知错误')}")
            
            img_base64 = data.get("img", "")
            uuid = data.get("uuid", "")
            
            if not img_base64 or not uuid:
                raise Exception("验证码数据不完整")
            
            img_bytes = base64.b64decode(img_base64)
            return img_bytes, uuid
            
        except requests.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("响应数据格式错误")
        except Exception:
            raise Exception("验证码图片解码失败")
    
    def login(self, username: str, password: str, code: str, uuid: str) -> str:
        """用户登录"""
        login_data = {
            "username": username,
            "password": password,
            "code": code,
            "uuid": uuid
        }
        
        try:
            response = self.session.post(
                Config.LOGIN_URL, 
                json=login_data, 
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") != 200:
                raise Exception(f"登录失败: {data.get('msg', '未知错误')}")
            
            token = data.get("token", "")
            if not token:
                raise Exception("未获取到有效的令牌")
            
            self.token = token
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            return token
            
        except requests.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("响应数据格式错误")
    
    def set_token(self, token: str):
        """设置令牌"""
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def get_profile(self) -> dict:
        """获取用户信息"""
        if not self.token:
            raise Exception("请先登录")
        
        try:
            response = self.session.get(Config.PROFILE_URL, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") != 200:
                raise Exception(f"获取用户信息失败: {data.get('msg', '未知错误')}")
            
            return data
            
        except requests.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("响应数据格式错误")
    
    def get_user_info(self) -> dict:
        """获取详细用户信息"""
        if not self.token:
            raise Exception("请先登录")
        
        try:
            response = self.session.get(Config.USER_INFO_URL, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") != 200:
                raise Exception(f"获取用户信息失败: {data.get('msg', '未知错误')}")
            
            return data
            
        except requests.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("响应数据格式错误")
    
    def logout(self) -> bool:
        """注销登录"""
        if not self.token:
            return True
        
        try:
            response = self.session.post(Config.LOGOUT_URL, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # 清除本地token和session header
            self.token = None
            if "Authorization" in self.session.headers:
                del self.session.headers["Authorization"]
            
            return True
            
        except requests.RequestException as e:
            # 即使请求失败，也清除本地token
            self.token = None
            if "Authorization" in self.session.headers:
                del self.session.headers["Authorization"]
            raise Exception(f"网络请求失败: {str(e)}")
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.token is not None
