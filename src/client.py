# -*- coding: utf-8 -*-
"""
豆包 AI 客户端模块

基于火山引擎官方 SDK 实现的流式聊天客户端，提供：
- 上下文对话管理
- 深度思考模式
- 联网搜索
- 流式输出
"""

from typing import Any, Dict, Iterator, Optional

from volcenginesdkarkruntime import Ark

from . import config
from .utils.id_mapper import get_id_mapper


def safe_decode_response(content: Any) -> Optional[str]:
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
    """豆包 AI 聊天客户端
    
    基于火山引擎 Responses API 实现。
    """
    
    def __init__(self):
        """初始化客户端"""
        self._validate_config()
        self._init_client()
        self._init_conversation_state()
        self.id_mapper = get_id_mapper()  # 获取ID映射器
    
    def _validate_config(self) -> None:
        """验证配置有效性"""
        if not config.ARK_API_KEY:
            raise ValueError(
                "请设置 ARK_API_KEY 环境变量或在 config.py 中配置 API 密钥"
            )
        if not config.ARK_ENDPOINT_ID:
            raise ValueError(
                "请设置 ARK_ENDPOINT_ID 环境变量或在 config.py 中配置端点 ID"
            )
    
    def _init_client(self) -> None:
        """初始化 Ark 客户端"""
        try:
            self.client = Ark(base_url=config.API_BASE_URL, api_key=config.ARK_API_KEY)
        except Exception as e:
            raise ValueError(f"初始化 Ark 客户端失败: {e}")
    
    def _init_conversation_state(self) -> None:
        """初始化对话状态"""
        self.previous_response_id: Optional[str] = None
        self.conversation_count: int = 0
        self.system_prompt: str = (
            config.GLOBAL_SYSTEM_PROMPT or "你是豆包，是由字节跳动开发的 AI 人工智能助手。"
        )
    
    def clear_history(self) -> None:
        """清空对话历史"""
        self.previous_response_id = None
        self.conversation_count = 0
    
    def set_response_id(self, short_id: str) -> None:
        """设置response_id，用于从指定对话点继续
        
        Args:
            short_id: 短id
        """
        # 将短id转换为长id
        long_id = self.id_mapper.get_long_id(short_id)
        if long_id:
            self.previous_response_id = long_id
        # 注意：这里不重置 conversation_count，因为我们是在继续之前的对话
    
    def get_conversation_length(self) -> int:
        """获取对话消息数量"""
        return self.conversation_count * 2
    
    def chat_stream(
        self,
        message: str,
        thinking_mode: str = "auto"
    ) -> Iterator[Optional[Dict[str, Any]]]:
        """发送聊天消息并获取流式回复
        
        Args:
            message: 用户消息
            thinking_mode: 思考模式 ('auto', 'enabled', 'disabled')
        
        Yields:
            包含回复内容的字典，可能的类型：
            - content: 普通回复内容
            - reasoning: 深度思考内容
            - web_search_*: 联网搜索事件
        """
        try:
            # 构建输入消息
            input_messages = self._build_input_messages(message)
            
            # 构建请求参数
            create_params = self._build_request_params(
                input_messages,
                thinking_mode
            )
            
            # 发送请求并处理流式响应
            response = self.client.responses.create(**create_params)
            yield from self._process_stream_response(response, thinking_mode)
            
        except Exception as e:
            print(f"流式聊天请求失败: {e}")
            yield None
    
    def _build_input_messages(self, message: str) -> list:
        """构建输入消息列表"""
        if self.previous_response_id is None:
            # 首次对话：包含system和user消息
            return [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message}
            ]
        else:
            # 后续对话：只需user消息
            return [{"role": "user", "content": message}]
    
    def _build_request_params(
        self,
        input_messages: list,
        thinking_mode: str
    ) -> dict:
        """构建API请求参数"""
        return {
            "model": config.ARK_ENDPOINT_ID,
            "input": input_messages,
            "previous_response_id": self.previous_response_id,
            "max_output_tokens": config.MAX_TOKENS,
            "temperature": config.TEMPERATURE,
            "top_p": config.TOP_P,
            "tools": [config.WEB_SEARCH_CONFIG],
            "stream": True,
            "store": True,
            "thinking": {"type": thinking_mode}
        }
    
    def _process_stream_response(
        self,
        response,
        thinking_mode: str
    ) -> Iterator[Optional[Dict[str, Any]]]:
        """处理流式响应"""
        response_id = None
        
        for chunk in response:
            chunk_type = getattr(chunk, "type", "")
            
            # 获取response_id
            if chunk_type == "response.created":
                if hasattr(chunk, "response") and hasattr(chunk.response, "id"):
                    response_id = chunk.response.id
            
            # 处理Web Search事件
            elif chunk_type == "response.web_search_call.in_progress":
                yield self._create_chunk_data('web_search_start', thinking_mode, response_id=response_id)
            
            elif chunk_type == "response.web_search_call.searching":
                search_query = getattr(chunk, "query", "")
                yield self._create_chunk_data('web_search_searching', thinking_mode, search_query=search_query, response_id=response_id)
            
            elif chunk_type == "response.web_search_call.completed":
                yield self._create_chunk_data('web_search_completed', thinking_mode, response_id=response_id)
            
            # 处理思考内容
            elif chunk_type == "response.reasoning_summary_text.delta":
                delta = getattr(chunk, "delta", "")
                if delta:
                    safe_reasoning = safe_decode_response(delta)
                    yield self._create_chunk_data('reasoning', thinking_mode, reasoning=safe_reasoning, response_id=response_id)
            
            # 处理回复内容
            elif chunk_type == "response.output_text.delta":
                delta = getattr(chunk, "delta", "")
                if delta:
                    safe_content = safe_decode_response(delta)
                    yield self._create_chunk_data('content', thinking_mode, content=safe_content, response_id=response_id)
        
        # 更新对话状态
        if response_id:
            self.previous_response_id = response_id
            self.conversation_count += 1
    
    @staticmethod
    def _create_chunk_data(
        chunk_type: str,
        thinking_mode: str,
        content: Optional[str] = None,
        reasoning: Optional[str] = None,
        search_query: str = "",
        response_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建chunk数据字典"""
        return {
            'type': chunk_type,
            'content': content,
            'reasoning': reasoning,
            'search_query': search_query,
            'thinking_mode': thinking_mode,
            'response_id': response_id
        }

