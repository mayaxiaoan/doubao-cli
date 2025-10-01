# -*- coding: utf-8 -*-
"""
豆包AI客户端类
基于火山引擎官方SDK的聊天客户端
"""

import os
import sys
from volcenginesdkarkruntime import Ark
from config import ARK_API_KEY, ARK_ENDPOINT_ID, API_BASE_URL, MAX_TOKENS, TEMPERATURE, TOP_P, SYMBOLS, COLORS, ENABLE_COLORS, AI_PERSONALITY, CURRENT_PERSONALITY, DEFAULT_THINKING_MODE, GLOBAL_RULES, ENABLE_GLOBAL_RULES


def colored_print(text, color_key='reset'):
    """带颜色的打印函数"""
    if ENABLE_COLORS and color_key in COLORS:
        colored_text = f"{COLORS[color_key]}{text}{COLORS['reset']}"
    else:
        colored_text = text
    
    # 处理Windows下的Unicode编码问题
    try:
        print(colored_text)
    except UnicodeEncodeError:
        # 如果遇到编码错误，使用ASCII安全的方式
        try:
            # 尝试用gbk编码，替换无法编码的字符
            safe_text = colored_text.encode('gbk', errors='replace').decode('gbk', errors='replace')
            print(safe_text)
        except:
            # 最后的备用方案：只保留ASCII字符
            ascii_text = ''.join(char if ord(char) < 128 else '?' for char in colored_text)
            print(ascii_text)


def safe_decode_response(content):
    """安全解码API响应内容"""
    if content is None:
        return None
    
    try:
        # 如果是bytes，进行解码
        if isinstance(content, bytes):
            return content.decode('utf-8', errors='replace')
        # 如果是字符串，确保编码正确
        elif isinstance(content, str):
            # 重新编码确保没有问题
            return content.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        else:
            return str(content)
    except Exception as e:
        colored_print(f"{SYMBOLS['warning']} 响应内容编码处理错误: {e}", 'system_warning')
        return str(content) if content else ""


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
            colored_print(f"{SYMBOLS['success']} 使用接入点: {self.endpoint_id}", 'system_success')
        except Exception as e:
            raise ValueError(f"初始化Ark客户端失败: {e}")
        
        # 测试API连接
        self._test_connection()
        
        # 初始化对话历史
        self.conversation_history = []
        self.current_personality = CURRENT_PERSONALITY
        self.system_message = AI_PERSONALITY.get(CURRENT_PERSONALITY, AI_PERSONALITY['default'])
        
        # 设置系统消息
        self._add_system_message()
    
    def _test_connection(self):
        """测试API连接是否正常"""
        try:
            colored_print(f"{SYMBOLS['connect']} 正在测试API连接...", 'system_info')
            
            # 发送一个简单的测试请求，使用独立的会话避免影响聊天上下文
            test_response = self.client.chat.completions.create(
                model=self.endpoint_id,
                messages=[
                    {"role": "system", "content": "你是一个测试助手，只需要简单回复'OK'即可。"},
                    {"role": "user", "content": "ping"}
                ],
                max_tokens=5,  # 只请求很少的token
                temperature=0.1,
                top_p=0.1
            )
            
            if test_response.choices and len(test_response.choices) > 0:
                colored_print(f"{SYMBOLS['success']} API连接测试成功", 'system_success')
            else:
                raise Exception("API响应格式异常")
                
        except Exception as e:
            error_msg = f"API连接测试失败: {e}"
            colored_print(f"{SYMBOLS['error']} {error_msg}", 'system_error')
            raise ValueError(error_msg)
    
    def _add_system_message(self):
        """添加系统消息"""
        if not self.conversation_history:  # 只在历史为空时添加
            # 构建完整的系统消息：全局规则 + AI身份
            full_system_message = self._build_system_message()
            self.conversation_history.append({
                "role": "system",
                "content": full_system_message
            })
    
    def _build_system_message(self):
        """构建完整的系统消息，包含全局规则和AI身份"""
        message_parts = []
        
        # 添加AI身份
        message_parts.append("=== AI身份 ===")
        message_parts.append(self.system_message)
        
        # 添加全局规则（如果启用）
        if ENABLE_GLOBAL_RULES and GLOBAL_RULES:
            message_parts.append("=== 全局规则 ===")
            for rule in GLOBAL_RULES:
                message_parts.append(f"• {rule}")
            message_parts.append("")  # 空行分隔
        
        
        return "\n".join(message_parts)
    
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
    
    def change_personality(self, personality_key):
        """
        切换AI身份
        
        Args:
            personality_key (str): 身份键名，必须在AI_PERSONALITY中存在
            
        Returns:
            bool: 切换成功返回True，失败返回False
        """
        if personality_key in AI_PERSONALITY:
            self.current_personality = personality_key
            self.system_message = AI_PERSONALITY[personality_key]
            # 重置对话历史并应用新身份（包含全局规则）
            self.clear_history()
            colored_print(f"{SYMBOLS['success']} AI身份已切换为: {personality_key}", 'system_success')
            return True
        else:
            colored_print(f"{SYMBOLS['error']} 未知的身份类型: {personality_key}", 'system_error')
            return False
    
    def get_personality_info(self):
        """
        获取当前AI身份信息
        
        Returns:
            dict: 包含当前身份信息的字典
        """
        return {
            'current': self.current_personality,
            'message': self.system_message,
            'available': list(AI_PERSONALITY.keys())
        }
    
    def show_available_personalities(self):
        """显示所有可用的AI身份"""
        colored_print(f"{SYMBOLS['info']} 可用的AI身份类型:", 'system_info')
        for key, description in AI_PERSONALITY.items():
            status = " [当前]" if key == self.current_personality else ""
            colored_print(f"  • {key}{status}: {description[:50]}{'...' if len(description) > 50 else ''}", 'system_info')
    
    def show_global_rules(self):
        """显示当前全局规则"""
        if ENABLE_GLOBAL_RULES and GLOBAL_RULES:
            colored_print(f"{SYMBOLS['info']} 当前全局规则:", 'system_info')
            for i, rule in enumerate(GLOBAL_RULES, 1):
                colored_print(f"  {i}. {rule}", 'system_info')
        else:
            colored_print(f"{SYMBOLS['info']} 全局规则已禁用", 'system_info')
    
    def get_system_message_preview(self):
        """获取系统消息预览（用于调试）"""
        return self._build_system_message()
    
    def health_check(self):
        """
        健康检查 - 测试API连接状态
        
        Returns:
            dict: 包含连接状态的字典
            {
                'status': str,        # 'healthy', 'unhealthy', 'unknown'
                'message': str,       # 状态描述
                'response_time': float # 响应时间（秒）
            }
        """
        import time
        
        try:
            start_time = time.time()
            
            # 发送一个简单的健康检查请求，使用独立的会话避免影响聊天上下文
            test_response = self.client.chat.completions.create(
                model=self.endpoint_id,
                messages=[
                    {"role": "system", "content": "你是一个测试助手，只需要简单回复'OK'即可。"},
                    {"role": "user", "content": "ping"}
                ],
                max_tokens=5,
                temperature=0.1,
                top_p=0.1
            )
            
            response_time = time.time() - start_time
            
            if test_response.choices and len(test_response.choices) > 0:
                return {
                    'status': 'healthy',
                    'message': 'API连接正常',
                    'response_time': round(response_time, 2)
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': 'API响应格式异常',
                    'response_time': round(response_time, 2)
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'连接失败: {str(e)}',
                'response_time': None
            }
    
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
                content = safe_decode_response(message_obj.content)
                
                # 检查是否有深度思考内容
                reasoning_content = None
                is_reasoning = False
                if hasattr(message_obj, 'reasoning_content') and message_obj.reasoning_content:
                    reasoning_content = safe_decode_response(message_obj.reasoning_content)
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
                        safe_content = safe_decode_response(delta.content)
                        full_content += safe_content
                        yield {
                            'content': safe_content,
                            'reasoning': None,
                            'type': 'content',
                            'thinking_mode': thinking_mode
                        }
                    
                    # 处理深度思考内容（如果有）
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None and delta.reasoning_content:
                        safe_reasoning = safe_decode_response(delta.reasoning_content)
                        full_reasoning += safe_reasoning
                        yield {
                            'content': None,
                            'reasoning': safe_reasoning,
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