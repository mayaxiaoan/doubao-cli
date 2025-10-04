# -*- coding: utf-8 -*-
"""
豆包AI客户端类
基于火山引擎官方SDK的聊天客户端
"""

from volcenginesdkarkruntime import Ark
from config import ARK_API_KEY, ARK_ENDPOINT_ID, API_BASE_URL, MAX_TOKENS, TEMPERATURE, TOP_P, GLOBAL_SYSTEM_PROMPT


def safe_decode_response(content):
    """安全解码API响应内容"""
    if content is None:
        return None
    
    try:
        if isinstance(content, bytes):
            return content.decode('utf-8', errors='replace')
        elif isinstance(content, str):
            return content
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
        except UnicodeDecodeError as e:
            raise ValueError(f"UTF-8编码错误: {e}")
        except Exception as e:
            raise ValueError(f"初始化Ark客户端失败: {e}")
        
        # Responses API 使用 previous_response_id 来管理对话历史
        # 不再需要手动维护完整的对话历史数组
        self.previous_response_id = None
        self.system_prompt = None  # 系统提示词
        self.conversation_count = 0  # 追踪对话轮数
        self._set_system_prompt()
    
    
    def _set_system_prompt(self):
        """设置系统提示词
        
        根据 Responses API 规范：
        - system prompt 应该通过 input 中的 {"role": "system", "content": "..."} 传入
        - instructions 参数用于临时覆盖之前的 system prompt（高级用法）
        """
        self.system_prompt = GLOBAL_SYSTEM_PROMPT if GLOBAL_SYSTEM_PROMPT else "你是豆包，是由字节跳动开发的 AI 人工智能助手。"
    
    def clear_history(self):
        """清空对话历史"""
        # Responses API 通过清空 previous_response_id 来重置对话
        self.previous_response_id = None
        self.conversation_count = 0
    
    def get_conversation_length(self):
        """获取对话轮数（返回消息数量，与旧版本兼容）"""
        # 每轮对话包含一个用户消息和一个助手回复，所以返回 count * 2
        return self.conversation_count * 2
    
    def chat_stream(self, message, thinking_mode="auto"):
        """发送聊天消息并获取流式回复（使用Responses API）
        
        Args:
            message: 用户消息
            thinking_mode: 思考模式 ('auto', 'enabled', 'disabled')
            enable_web_search: 是否启用网络搜索。None表示自动检测，True强制启用，False禁用
            override_instructions: 临时覆盖 system prompt 的指令（高级用法）
                注意：使用 instructions 参数会导致无法使用缓存功能
        
        Responses API 正确用法示例：
            # 首次对话：自动包含 system prompt
            for chunk in client.chat_stream("你好"):
                ...
            
            # 后续对话：通过 previous_response_id 自动引用历史
            for chunk in client.chat_stream("继续聊"):
                ...
            
            # 临时覆盖 system prompt（例如切换角色）
            for chunk in client.chat_stream("人之初", 
                override_instructions="你只能用三个字回答"):
                ...
        """
        try:
            # Responses API 的正确用法（根据官方文档）：
            # 1. 首次对话：input = [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            # 2. 后续对话：input = [{"role": "user", "content": "..."}] + previous_response_id
            # 3. instructions 参数用于临时覆盖 system prompt（可选）
            # 4. tools 参数按需启用（如 web_search），启用后 AI 自动判断是否调用
            # 5. 设置 store=True 以便存储响应供后续引用
            
            # 构建 input 参数
            if self.previous_response_id is None:
                # 首次对话：包含 system 和 user 消息
                input_messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message}
                ]
            else:
                # 后续对话：只需 user 消息
                input_messages = [{"role": "user", "content": message}]
            
            # 构建请求参数
            create_params = {
                "model": ARK_ENDPOINT_ID,
                "input": input_messages,
                "previous_response_id": self.previous_response_id,  # 引用上一次对话
                "max_output_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "top_p": TOP_P,
                "tools": [
                    # 配置Web Search工具参数
                    {
                        "type": "web_search",
                        "limit": 10,  # 最多返回10条搜索结果
                        "sources": ["toutiao", "douyin", "moji"],  # 优先从头条、抖音、知乎搜索
                        "user_location": {  # 优化地域相关搜索结果（如国内城市）
                            "type": "approximate",
                            "country": "中国",
                            "region": "上海",
                            "city": "上海"
                        }
                    }
                ],
                "stream": True,
                "store": True,  # 存储响应以便后续引用
                "thinking": {"type": thinking_mode}
            }
            
            
            response = self.client.responses.create(**create_params)
            
            full_content = ""
            response_id = None
            
            # 遍历API原始流式回复（responses端点格式）
            for chunk in response:
                chunk_type = getattr(chunk, "type", "")
                
                # 获取 response_id（用于下一轮对话）
                if chunk_type == "response.created":
                    # response.created 事件包含 response 对象，其中有 id 字段
                    if hasattr(chunk, "response") and hasattr(chunk.response, "id"):
                        response_id = chunk.response.id
                
                # 处理 Web Search 事件
                elif chunk_type == "response.web_search_call.in_progress":
                    yield {
                        'content': None,
                        'reasoning': None,
                        'type': 'web_search_start',
                        'thinking_mode': thinking_mode
                    }
                
                elif chunk_type == "response.web_search_call.searching":
                    # 可以提取搜索查询信息
                    search_query = getattr(chunk, "query", "") if hasattr(chunk, "query") else ""
                    yield {
                        'content': None,
                        'reasoning': None,
                        'type': 'web_search_searching',
                        'search_query': search_query,
                        'thinking_mode': thinking_mode
                    }
                
                elif chunk_type == "response.web_search_call.completed":
                    yield {
                        'content': None,
                        'reasoning': None,
                        'type': 'web_search_completed',
                        'thinking_mode': thinking_mode
                    }
                
                # 处理思考内容
                elif chunk_type == "response.reasoning_summary_text.delta":
                    delta = getattr(chunk, "delta", "")
                    if delta:
                        safe_reasoning = safe_decode_response(delta)
                        yield {
                            'content': None,
                            'reasoning': safe_reasoning,
                            'type': 'reasoning',
                            'thinking_mode': thinking_mode
                        }
                
                # 处理正常回复内容
                elif chunk_type == "response.output_text.delta":
                    delta = getattr(chunk, "delta", "")
                    if delta:
                        safe_content = safe_decode_response(delta)
                        full_content += safe_content
                        yield {
                            'content': safe_content,
                            'reasoning': None,
                            'type': 'content',
                            'thinking_mode': thinking_mode
                        }
            
            # 更新 previous_response_id 以便下次对话使用
            if response_id:
                self.previous_response_id = response_id
                self.conversation_count += 1  # 成功完成一轮对话
                        
        except Exception as e:
            print(f"流式聊天请求失败: {e}")
            yield None