# -*- coding: utf-8 -*-
"""
豆包AI客户端类
基于火山引擎官方SDK的聊天客户端
"""

import os
from volcenginesdkarkruntime import Ark
from config import ARK_API_KEY, ARK_ENDPOINT_ID, API_BASE_URL, MAX_TOKENS, TEMPERATURE, TOP_P


class DoubaoClient:
    """豆包AI聊天客户端（基于官方SDK）"""
    
    def __init__(self):
        """初始化客户端"""
        self.api_key = ARK_API_KEY
        self.endpoint_id = ARK_ENDPOINT_ID
        
        # 验证配置
        if not self.api_key or self.api_key == "your_api_key_here":
            raise ValueError("请在config.py中设置有效的API_KEY或设置环境变量ARK_API_KEY")
        if not self.endpoint_id or self.endpoint_id == "your_endpoint_id_here":
            raise ValueError("请在config.py中设置有效的ENDPOINT_ID或设置环境变量ARK_ENDPOINT_ID")
        
        # 初始化Ark客户端
        try:
            self.client = Ark(
                base_url=API_BASE_URL,
                api_key=self.api_key,
            )
            print(f"✅ 使用接入点: {self.endpoint_id}")
        except Exception as e:
            raise ValueError(f"初始化Ark客户端失败: {e}")
    
    def chat(self, message):
        """
        发送聊天消息并获取回复（非流式）
        
        Args:
            message (str): 用户输入的消息
            
        Returns:
            str: AI的回复内容，如果失败则返回None
        """
        try:
            response = self.client.chat.completions.create(
                model=self.endpoint_id,
                messages=[
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                # 启用推理会话应用层加密（可选）
                extra_headers={'x-is-encrypted': 'true'}
            )
            
            # 提取AI回复内容
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                print("API响应格式异常：未找到choices")
                return None
                
        except Exception as e:
            print(f"聊天请求失败: {e}")
            # 打印更详细的错误信息用于调试
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            return None
    
    def chat_stream(self, message):
        """
        发送聊天消息并获取流式回复（逐字显示）
        
        Args:
            message (str): 用户输入的消息
            
        Yields:
            str: AI的回复内容片段
        """
        try:
            response = self.client.chat.completions.create(
                model=self.endpoint_id,
                messages=[
                    {
                        "role": "user", 
                        "content": message
                    }
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                stream=True,  # 启用流式输出
                # 启用推理会话应用层加密（可选）
                extra_headers={'x-is-encrypted': 'true'}
            )
            
            # 处理流式响应
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content is not None and delta.content:
                        # 只返回非空内容，过滤掉空字符串
                        yield delta.content
                        
        except Exception as e:
            print(f"流式聊天请求失败: {e}")
            # 打印更详细的错误信息用于调试
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            yield None