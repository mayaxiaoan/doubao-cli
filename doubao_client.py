# -*- coding: utf-8 -*-
"""
豆包AI客户端类
基于火山引擎官方SDK的聊天客户端
"""

import os
from volcenginesdkarkruntime import Ark
from config import ARK_API_KEY, ARK_ENDPOINT_ID, API_BASE_URL, MAX_TOKENS, TEMPERATURE, TOP_P


class DoubaoClient:
    """豆包AI聊天客户端（基于官方SDK，支持上下文对话）"""
    
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
        
        # 初始化对话历史
        self.conversation_history = []
        self.system_message = "你是豆包，是由字节跳动开发的 AI 人工智能助手。"
        
        # 设置系统消息
        self._add_system_message()
    
    def _add_system_message(self):
        """添加系统消息"""
        if not self.conversation_history:  # 只在历史为空时添加
            self.conversation_history.append({
                "role": "system",
                "content": self.system_message
            })
    
    def add_user_message(self, message):
        """添加用户消息到对话历史"""
        self.conversation_history.append({
            "role": "user", 
            "content": message
        })
    
    def add_assistant_message(self, message):
        """添加助手回复到对话历史"""
        self.conversation_history.append({
            "role": "assistant",
            "content": message
        })
    
    def clear_history(self):
        """清空对话历史，但保留系统消息"""
        self.conversation_history = []
        self._add_system_message()
    
    def get_conversation_length(self):
        """获取对话轮数（不包含系统消息）"""
        return len([msg for msg in self.conversation_history if msg["role"] != "system"])
    
    def chat(self, message, thinking_mode="auto"):
        """
        发送聊天消息并获取回复（非流式，支持上下文对话）
        
        Args:
            message (str): 用户输入的消息
            thinking_mode (str): 深度思考模式，可选值：
                - "auto": 模型自行判断是否使用深度思考能力（默认）
                - "enabled": 强制使用深度思考能力
                - "disabled": 不使用深度思考能力
            
        Returns:
            dict: 包含回复内容和深度思考的字典，失败则返回None
            {
                'content': str,           # 回复内容
                'reasoning': str or None, # 深度思考内容（如果有）
                'is_reasoning': bool      # 是否触发了深度思考
                'thinking_mode': str      # 使用的思考模式
            }
        """
        try:
            # 添加用户消息到历史
            self.add_user_message(message)
            
            response = self.client.chat.completions.create(
                model=self.endpoint_id,
                messages=self.conversation_history,  # 使用完整对话历史
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                thinking={"type": thinking_mode},  # 控制深度思考模式
                # 启用推理会话应用层加密（可选）
                extra_headers={'x-is-encrypted': 'true'}
            )
            
            # 提取AI回复内容
            if response.choices and len(response.choices) > 0:
                message_obj = response.choices[0].message
                content = message_obj.content
                
                # 检查是否有深度思考内容
                reasoning_content = None
                is_reasoning = False
                if hasattr(message_obj, 'reasoning_content') and message_obj.reasoning_content:
                    reasoning_content = message_obj.reasoning_content
                    is_reasoning = True
                
                # 添加助手回复到历史
                self.add_assistant_message(content)
                
                return {
                    'content': content,
                    'reasoning': reasoning_content,
                    'is_reasoning': is_reasoning,
                    'thinking_mode': thinking_mode
                }
            else:
                print("API响应格式异常：未找到choices")
                return None
                
        except Exception as e:
            print(f"聊天请求失败: {e}")
            # 打印更详细的错误信息用于调试
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            return None
    
    def chat_stream(self, message, thinking_mode="auto"):
        """
        发送聊天消息并获取流式回复（逐字显示，支持上下文对话）
        
        Args:
            message (str): 用户输入的消息
            thinking_mode (str): 深度思考模式，可选值：
                - "auto": 模型自行判断是否使用深度思考能力（默认）
                - "enabled": 强制使用深度思考能力
                - "disabled": 不使用深度思考能力
            
        Yields:
            dict: 包含内容片段和元信息的字典
            {
                'content': str,           # 内容片段
                'reasoning': str or None, # 深度思考片段（如果有）
                'type': str,             # 'content' 或 'reasoning'
                'thinking_mode': str     # 使用的思考模式
            }
        """
        try:
            # 添加用户消息到历史
            self.add_user_message(message)
            
            response = self.client.chat.completions.create(
                model=self.endpoint_id,
                messages=self.conversation_history,  # 使用完整对话历史
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                stream=True,  # 启用流式输出
                thinking={"type": thinking_mode},  # 控制深度思考模式
                # 启用推理会话应用层加密（可选）
                extra_headers={'x-is-encrypted': 'true'}
            )
            
            # 用于收集完整的回复内容
            full_content = ""
            full_reasoning = ""
            
            # 处理流式响应
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    
                    # 处理普通回复内容
                    if hasattr(delta, 'content') and delta.content is not None and delta.content:
                        full_content += delta.content
                        yield {
                            'content': delta.content,
                            'reasoning': None,
                            'type': 'content',
                            'thinking_mode': thinking_mode
                        }
                    
                    # 处理深度思考内容（如果有）
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None and delta.reasoning_content:
                        full_reasoning += delta.reasoning_content
                        yield {
                            'content': None,
                            'reasoning': delta.reasoning_content,
                            'type': 'reasoning',
                            'thinking_mode': thinking_mode
                        }
            
            # 流式输出完成后，将完整回复添加到历史
            if full_content:
                self.add_assistant_message(full_content)
                        
        except Exception as e:
            print(f"流式聊天请求失败: {e}")
            # 打印更详细的错误信息用于调试
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            yield None