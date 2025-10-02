# -*- coding: utf-8 -*-
"""
豆包AI客户端类
基于火山引擎官方SDK的聊天客户端
"""

from volcenginesdkarkruntime import Ark
from config import ARK_API_KEY, ARK_ENDPOINT_ID, API_BASE_URL, MAX_TOKENS, TEMPERATURE, TOP_P, GLOBAL_RULES, ENABLE_GLOBAL_RULES


def safe_decode_response(content):
    """安全解码API响应内容"""
    if content is None:
        return None
    
    try:
        if isinstance(content, bytes):
            return content.decode('utf-8', errors='replace')
        elif isinstance(content, str):
            return content.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        else:
            return str(content)
    except Exception:
        return str(content) if content else ""


class DoubaoClient:
    """豆包AI聊天客户端（基于官方SDK，支持上下文对话）"""
    
    def __init__(self):
        """初始化客户端"""
        # 验证配置
        if not ARK_API_KEY or ARK_API_KEY == "your_api_key_here":
            raise ValueError("请在config.py中设置有效的API_KEY")
        if not ARK_ENDPOINT_ID or ARK_ENDPOINT_ID == "your_endpoint_id_here":
            raise ValueError("请在config.py中设置有效的ENDPOINT_ID")
        
        # 初始化Ark客户端
        try:
            self.client = Ark(base_url=API_BASE_URL, api_key=ARK_API_KEY)
        except Exception as e:
            raise ValueError(f"初始化Ark客户端失败: {e}")
        
        # 初始化对话历史
        self.conversation_history = []
        self._add_system_message()
    
    
    def _add_system_message(self):
        """添加系统消息"""
        if not self.conversation_history:
            system_content = "\n".join(GLOBAL_RULES) if ENABLE_GLOBAL_RULES and GLOBAL_RULES else "你是豆包，是由字节跳动开发的 AI 人工智能助手。"
            self.conversation_history.append({"role": "system", "content": system_content})
    
    def add_user_message(self, message):
        """添加用户消息到对话历史"""
        self.conversation_history.append({"role": "user", "content": message})
    
    def add_assistant_message(self, message):
        """添加助手回复到对话历史"""
        self.conversation_history.append({"role": "assistant", "content": message})
    
    def clear_history(self):
        """清空对话历史，但保留系统消息"""
        self.conversation_history = []
        self._add_system_message()
    
    def get_conversation_length(self):
        """获取对话轮数（不包含系统消息）"""
        return len([msg for msg in self.conversation_history if msg["role"] != "system"])
    
    def chat_stream(self, message, thinking_mode="auto"):
        """发送聊天消息并获取流式回复"""
        try:
            self.add_user_message(message)
            
            response = self.client.chat.completions.create(
                model=ARK_ENDPOINT_ID,
                messages=self.conversation_history,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                stream=True,
                thinking={"type": thinking_mode}
            )
            
            full_content = ""
            
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    
                    # 处理普通回复内容
                    if hasattr(delta, 'content') and delta.content:
                        safe_content = safe_decode_response(delta.content)
                        full_content += safe_content
                        yield {
                            'content': safe_content,
                            'reasoning': None,
                            'type': 'content',
                            'thinking_mode': thinking_mode
                        }
                    
                    # 处理深度思考内容
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                        safe_reasoning = safe_decode_response(delta.reasoning_content)
                        yield {
                            'content': None,
                            'reasoning': safe_reasoning,
                            'type': 'reasoning',
                            'thinking_mode': thinking_mode
                        }
            
            # 将完整回复添加到历史
            if full_content:
                self.add_assistant_message(full_content)
                        
        except Exception as e:
            print(f"流式聊天请求失败: {e}")
            yield None