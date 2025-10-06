# -*- coding: utf-8 -*-
"""
API 密钥管理模块

负责 API 密钥的存储、读取和验证。
密钥以明文形式保存在 api_keys.ini 中，方便编辑。
"""

import os
from pathlib import Path
from typing import Optional, Tuple


class KeyManager:
    """API 密钥管理器"""
    
    def __init__(self, key_file: str = "api_keys.ini"):
        """初始化密钥管理器
        
        Args:
            key_file: 密钥文件路径（相对于项目根目录）
        """
        self.key_file = Path(key_file)
        self.api_key: Optional[str] = None
        self.endpoint_id: Optional[str] = None
    
    def key_file_exists(self) -> bool:
        """检查密钥文件是否存在
        
        Returns:
            如果密钥文件存在返回 True，否则返回 False
        """
        return self.key_file.exists()
    
    def load_keys(self) -> bool:
        """从文件加载密钥
        
        Returns:
            加载成功返回 True，失败返回 False
        """
        if not self.key_file_exists():
            return False
        
        try:
            with open(self.key_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 解析密钥文件
            for line in lines:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                
                # 解析 key = value 格式（兼容有无空格）
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'ARK_API_KEY':
                        self.api_key = value
                    elif key == 'ARK_ENDPOINT_ID':
                        self.endpoint_id = value
            
            # 验证是否成功读取到密钥
            return bool(self.api_key and self.endpoint_id)
            
        except Exception as e:
            print(f"读取密钥文件失败: {e}")
            return False
    
    def save_keys(self, api_key: str, endpoint_id: str) -> bool:
        """保存密钥到文件
        
        Args:
            api_key: API 密钥
            endpoint_id: 端点 ID
        
        Returns:
            保存成功返回 True，失败返回 False
        """
        try:
            content = f"""# 豆包 AI API 密钥配置
# 警告：此文件包含敏感信息，请勿上传到版本库！

[API]
ARK_API_KEY = {api_key}
ARK_ENDPOINT_ID = {endpoint_id}

# 说明：
# - 可直接编辑此文件修改密钥
# - 修改后重启程序生效
# - 请妥善保管，不要分享
"""
            
            with open(self.key_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.api_key = api_key
            self.endpoint_id = endpoint_id
            return True
            
        except Exception as e:
            print(f"保存密钥文件失败: {e}")
            return False
    
    def get_keys(self) -> Tuple[Optional[str], Optional[str]]:
        """获取密钥
        
        Returns:
            (api_key, endpoint_id) 元组
        """
        return self.api_key, self.endpoint_id
    
    def validate_keys(self) -> bool:
        """验证密钥是否有效（非空且格式合理）
        
        Returns:
            密钥有效返回 True，否则返回 False
        """
        if not self.api_key or not self.endpoint_id:
            return False
        
        # 基本格式验证
        if len(self.api_key) < 10 or len(self.endpoint_id) < 5:
            return False
        
        return True
    
    def prompt_for_keys(self) -> bool:
        """提示用户输入密钥
        
        Returns:
            用户输入并保存成功返回 True，否则返回 False
        """
        print("\n" + "=" * 70)
        print("  欢迎使用豆包 AI 聊天程序！")
        print("=" * 70)
        print("\n检测到这是你第一次运行本程序，需要配置 API 密钥。")
        print("\n请按照以下步骤获取密钥：")
        print("  1. 访问火山引擎豆包 AI 官网")
        print("  2. 注册并登录账号")
        print("  3. 创建应用并获取 API 密钥和端点 ID")
        print("\n" + "-" * 70)
        
        try:
            # 获取 API 密钥
            print("\n请输入你的 API 密钥 (ARK_API_KEY):")
            api_key = input("API Key: ").strip()
            
            if not api_key:
                print("❌ API 密钥不能为空！")
                return False
            
            # 获取端点 ID
            print("\n请输入你的端点 ID (ARK_ENDPOINT_ID):")
            endpoint_id = input("Endpoint ID: ").strip()
            
            if not endpoint_id:
                print("❌ 端点 ID 不能为空！")
                return False
            
            # 保存密钥
            print("\n正在保存密钥...")
            if self.save_keys(api_key, endpoint_id):
                print(f"✅ 密钥已保存到 {self.key_file}")
                print("\n" + "-" * 70)
                print("说明：")
                print(f"  - 密钥已保存在 {self.key_file}")
                print("  - 可随时编辑该文件修改密钥")
                print("  - 请勿上传到版本库或分享给他人")
                print("=" * 70 + "\n")
                return True
            else:
                print("❌ 保存密钥失败！")
                return False
                
        except KeyboardInterrupt:
            print("\n\n用户取消输入")
            return False
        except Exception as e:
            print(f"\n❌ 输入过程出错: {e}")
            return False


# 全局密钥管理器实例
_global_key_manager: Optional[KeyManager] = None


def get_key_manager() -> KeyManager:
    """获取全局密钥管理器实例
    
    Returns:
        全局 KeyManager 实例
    """
    global _global_key_manager
    if _global_key_manager is None:
        _global_key_manager = KeyManager()
    return _global_key_manager

