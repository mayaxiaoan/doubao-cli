# -*- coding: utf-8 -*-
"""
命令处理模块

负责解析和执行用户命令，包括：
- 聊天命令
- 历史记录管理
- 对话上下文切换
- 深度思考模式控制
"""

from typing import Dict, Any, Optional

from .config import SYMBOLS, DEFAULT_THINKING_MODE


class CommandResult:
    """命令执行结果封装类"""
    
    def __init__(
        self,
        cmd_type: str,
        message: str = "",
        response: Optional[str] = None,
        thinking_mode: str = DEFAULT_THINKING_MODE,
        thinking_status: str = "",
        target_response_id: Optional[str] = None,
        **kwargs
    ):
        self.type = cmd_type
        self.message = message
        self.response = response
        self.thinking_mode = thinking_mode
        self.thinking_status = thinking_status
        self.target_response_id = target_response_id
        self.extra = kwargs
    
    def __getitem__(self, key: str):
        """支持字典式访问"""
        if key == 'type':
            return self.type
        elif key == 'message':
            return self.message
        elif key == 'response':
            return self.response
        elif key == 'thinking_mode':
            return self.thinking_mode
        elif key == 'thinking_status':
            return self.thinking_status
        elif key == 'target_response_id':
            return self.target_response_id
        else:
            return self.extra.get(key)
    
    def __setitem__(self, key: str, value):
        """支持字典式赋值"""
        if key == 'type':
            self.type = value
        elif key == 'message':
            self.message = value
        elif key == 'response':
            self.response = value
        elif key == 'thinking_mode':
            self.thinking_mode = value
        elif key == 'thinking_status':
            self.thinking_status = value
        elif key == 'target_response_id':
            self.target_response_id = value
        else:
            self.extra[key] = value
    
    def get(self, key: str, default=None):
        """支持字典式get方法"""
        try:
            return self[key]
        except KeyError:
            return default


class CommandHandler:
    """命令处理器
    
    统一处理用户输入的各种命令。
    """
    
    @staticmethod
    def parse(user_input: str) -> CommandResult:
        """解析用户命令
        
        Args:
            user_input: 用户输入的原始字符串
        
        Returns:
            CommandResult: 命令执行结果
        """
        # 不是命令，直接返回普通聊天
        if not user_input.startswith('#'):
            return CommandResult('chat', message=user_input)
        
        # 解析命令和内容
        parts = user_input[1:].split(' ', 1)
        command = parts[0].lower()
        message = parts[1] if len(parts) > 1 else ''
        
        # 路由到具体的命令处理器
        handler_map = {
            'exit': CommandHandler._handle_exit,
            'quit': CommandHandler._handle_exit,
            '退出': CommandHandler._handle_exit,
            '再见': CommandHandler._handle_exit,
            'clear': CommandHandler._handle_clear,
            'new': CommandHandler._handle_clear,
            '新话题': CommandHandler._handle_clear,
            'think': CommandHandler._handle_think,
            'fast': CommandHandler._handle_fast,
            'chat': CommandHandler._handle_continue,
            'continue': CommandHandler._handle_continue,
            'c': CommandHandler._handle_continue,
            '对话': CommandHandler._handle_continue,
            'history': CommandHandler._handle_history,
            'h': CommandHandler._handle_history,
            '历史': CommandHandler._handle_history,
            'hdel': CommandHandler._handle_delete,
            'delete': CommandHandler._handle_delete,
            '删除': CommandHandler._handle_delete,
        }
        
        handler = handler_map.get(command)
        if handler:
            return handler(message)
        
        # 未知命令，当作普通消息处理
        return CommandResult('chat', message=user_input)
    
    @staticmethod
    def _handle_exit(message: str) -> CommandResult:
        """处理退出命令"""
        return CommandResult(
            'exit',
            response=f"{SYMBOLS['goodbye']} 感谢使用豆包AI聊天程序，再见！"
        )
    
    @staticmethod
    def _handle_clear(message: str) -> CommandResult:
        """处理清空历史命令"""
        if not message.strip():
            return CommandResult(
                'error',
                response=f"{SYMBOLS['warning']} 请在命令后输入新的聊天内容"
            )
        
        return CommandResult(
            'clear',
            message=message,
            response=f"{SYMBOLS['success']} 对话历史已清空，我们可以开始新的聊天话题"
        )
    
    @staticmethod
    def _handle_think(message: str) -> CommandResult:
        """处理深度思考命令"""
        if not message.strip():
            return CommandResult(
                'error',
                response=f"{SYMBOLS['warning']} 请在命令后输入有效的消息"
            )
        
        return CommandResult(
            'chat',
            message=message,
            thinking_mode='enabled',
            thinking_status=' [要求深度思考]'
        )
    
    @staticmethod
    def _handle_fast(message: str) -> CommandResult:
        """处理快速回复命令"""
        if not message.strip():
            return CommandResult(
                'error',
                response=f"{SYMBOLS['warning']} 请在命令后输入有效的消息"
            )
        
        return CommandResult(
            'chat',
            message=message,
            thinking_mode='disabled',
            thinking_status=' [快速回复]'
        )
    
    @staticmethod
    def _handle_continue(message: str) -> CommandResult:
        """处理继续对话命令"""
        # 解析格式：#chat 对话id 消息内容（对话id可以是短id）
        chat_parts = message.split(' ', 1)
        
        if len(chat_parts) < 1 or not chat_parts[0].strip():
            return CommandResult(
                'error',
                response=f"{SYMBOLS['warning']} 命令格式错误！正确格式：#chat 对话id 消息内容"
            )
        
        target_response_id = chat_parts[0].strip()
        actual_message = chat_parts[1].strip() if len(chat_parts) > 1 else ''
        
        if not actual_message:
            return CommandResult(
                'error',
                response=f"{SYMBOLS['warning']} 请在对话id后输入有效的消息"
            )
        
        return CommandResult(
            'chat',
            message=actual_message,
            target_response_id=target_response_id,
            thinking_status=f' [继续对话:{target_response_id}]'
        )
    
    @staticmethod
    def _handle_history(message: str) -> CommandResult:
        """处理查看历史命令"""
        try:
            num_turns = int(message) if message.strip().isdigit() else 10
            return CommandResult('history', history_turns=num_turns)
        except ValueError:
            return CommandResult(
                'error',
                response=f"{SYMBOLS['warning']} 命令格式错误！正确格式：#history 数字（可选）"
            )
    
    @staticmethod
    def _handle_delete(message: str) -> CommandResult:
        """处理删除历史命令"""
        if not message.strip():
            return CommandResult(
                'error',
                response=f"{SYMBOLS['warning']} 请指定要删除的轮数！格式：#hdel 数字"
            )
        
        try:
            num_turns = int(message.strip())
            if num_turns <= 0:
                return CommandResult(
                    'error',
                    response=f"{SYMBOLS['warning']} 删除轮数必须大于0"
                )
            
            return CommandResult('hdel', delete_turns=num_turns)
        except ValueError:
            return CommandResult(
                'error',
                response=f"{SYMBOLS['warning']} 命令格式错误！正确格式：#hdel 数字"
            )


def parse_command(user_input: str) -> CommandResult:
    """解析用户命令（向后兼容接口）
    
    Args:
        user_input: 用户输入字符串
    
    Returns:
        命令执行结果字典
    """
    return CommandHandler.parse(user_input)

