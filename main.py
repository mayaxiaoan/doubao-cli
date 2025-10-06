# -*- coding: utf-8 -*-
"""
豆包AI聊天程序主入口

使用方法：
    python main.py
"""

import sys
import threading

from src.client import DoubaoClient
from src.config import SYMBOLS, COLORS, DEFAULT_THINKING_MODE, HISTORY_MAX_TURNS
from src.utils import setup_encoding, get_battery_monitor, InputHandler, get_chat_history
from src.ui import (
    colored_print,
    print_welcome,
    print_usage,
    waiting_animation,
    StreamOutputHandler
)


def parse_command(user_input: str):
    """统一解析用户命令
    """
    result = {
        'type': 'chat',
        'message': user_input,
        'thinking_mode': DEFAULT_THINKING_MODE,
        'thinking_status': '',
        'response': None,
        'target_response_id': None
    }
    
    # 不是命令，直接返回普通聊天
    if not user_input.startswith('#'):
        return result
    
    # 解析命令和内容
    parts = user_input[1:].split(' ', 1)  # 移除 # 并按第一个空格分割
    command = parts[0].lower()
    message = parts[1] if len(parts) > 1 else ''
    
    # 退出命令
    if command in ['exit', 'quit', '退出', '再见']:
        result['type'] = 'exit'
        result['response'] = f"{SYMBOLS['goodbye']} 感谢使用豆包AI聊天程序，再见！"
        return result
    
    # 清空历史命令
    if command in ['clear', 'new', '新话题']:
        # 检查是否提供了新的聊天内容
        if not message.strip():
            result['type'] = 'error'
            result['response'] = f"{SYMBOLS['warning']} 请在命令后输入新的聊天内容"
            return result
        
        result['type'] = 'clear'
        result['message'] = message
        result['response'] = f"{SYMBOLS['success']} 对话历史已清空，我们可以开始新的聊天话题"
        return result
    
    # 深度思考模式
    if command == 'think':
        if not message.strip():
            result['type'] = 'error'
            result['response'] = f"{SYMBOLS['warning']} 请在命令后输入有效的消息"
            return result
        
        result['type'] = 'chat'
        result['message'] = message
        result['thinking_mode'] = 'enabled'
        result['thinking_status'] = ' [要求深度思考]'
        return result
    
    # 快速回复模式
    if command == 'fast':
        if not message.strip():
            result['type'] = 'error'
            result['response'] = f"{SYMBOLS['warning']} 请在命令后输入有效的消息"
            return result
        
        result['type'] = 'chat'
        result['message'] = message
        result['thinking_mode'] = 'disabled'
        result['thinking_status'] = ' [快速回复]'
        return result
    
    # 从指定response_id继续对话
    if command in ['chat', 'continue', 'c', '对话']:
        # 解析格式：#chat 对话id 消息内容（对话id可以是短id）
        chat_parts = message.split(' ', 1)
        if len(chat_parts) >= 1:
            target_response_id = chat_parts[0].strip()
            actual_message = chat_parts[1].strip() if len(chat_parts) > 1 else ''
            
            # 检查对话id是否存在
            if not target_response_id:
                result['type'] = 'error'
                result['response'] = f"{SYMBOLS['warning']} 命令格式错误！正确格式：#chat 对话id 消息内容"
                return result
            
            # 检查消息内容是否存在
            if not actual_message:
                result['type'] = 'error'
                result['response'] = f"{SYMBOLS['warning']} 请在对话id后输入有效的消息"
                return result
            
            result['type'] = 'chat'
            result['message'] = actual_message
            result['target_response_id'] = target_response_id
            result['thinking_status'] = f' [继续对话:{target_response_id}]'
            return result
        
        # 格式错误，提示用户
        result['type'] = 'error'
        result['response'] = f"{SYMBOLS['warning']} 命令格式错误！正确格式：#chat 对话id 消息内容"
        return result
    
    # 查看历史记录命令
    if command in ['history', 'h', '历史']:
        try:
            # 默认显示10轮，用户可以指定数量
            num_turns = int(message) if message.strip().isdigit() else 10
            result['type'] = 'history'
            result['history_turns'] = num_turns
            return result
        except ValueError:
            result['type'] = 'error'
            result['response'] = f"{SYMBOLS['warning']} 命令格式错误！正确格式：#history 数字（可选）"
            return result
    
    # 未知命令，当作普通消息处理
    result['message'] = user_input
    return result


def display_history(num_turns: int) -> None:
    """显示历史聊天记录
    
    Args:
        num_turns: 要显示的轮次数
    """
    history = get_chat_history(HISTORY_MAX_TURNS)
    records = history.get_recent_history(num_turns)
    
    if not records:
        colored_print(f"{SYMBOLS['info']} 暂无历史记录", 'system_info')
        return
    
    colored_print(f"\n{SYMBOLS['star']} {SYMBOLS['separator'] * 20} 历史记录（最近{len(records)}轮）{SYMBOLS['separator'] * 20} {SYMBOLS['star']}", 'separator_line')
    
    for record in records:
        record_type = record.get('type')
        timestamp = record.get('timestamp', '')
        
        if record_type == 'chat':
            # 显示聊天记录
            short_id = record.get('short_id', '?')
            user_msg = record.get('user_message', '')
            bot_reply = record.get('bot_reply', '')
            
            colored_print(f"\n[{timestamp}] ({short_id})", 'system_info')
            colored_print(f" 您: {user_msg}", 'user_text')
            colored_print(f" 豆包: {bot_reply}", 'cyan')
        
        elif record_type == 'command':
            # 显示命令记录
            command = record.get('command', '')
            message = record.get('message', '')
            colored_print(f"\n[{timestamp}] 命令: #{command}", 'system_warning')
            colored_print(f"  {message}", 'system_info')
    
    colored_print(f"\n{SYMBOLS['star']} {SYMBOLS['separator'] * 60} {SYMBOLS['star']}\n", 'separator_line')


def process_ai_response(
    client: DoubaoClient,
    message: str,
    thinking_mode: str,
    thinking_status: str
) -> tuple:
    """处理AI流式响应
    
    Args:
        client: 豆包客户端
        message: 用户消息
        thinking_mode: 思考模式
        thinking_status: 思考状态标记
    
    Returns:
        (short_id, bot_reply): 短id和AI回复内容（不含思考部分）
    """
    # 启动等待动画
    stop_animation = threading.Event()
    animation_thread = threading.Thread(
        target=waiting_animation,
        args=(stop_animation,)
    )
    animation_thread.daemon = True
    animation_thread.start()
    
    try:
        output_handler = StreamOutputHandler()
        
        # 处理流式回复
        for chunk_data in client.chat_stream(message, thinking_mode):
            output_handler.process_chunk(chunk_data, stop_animation, thinking_status)
        
        # 完成输出
        output_handler.finalize(stop_animation)
        
        # 返回短id和回复内容
        return output_handler.get_short_id(), output_handler.get_bot_reply()
        
    except Exception as e:
        stop_animation.set()
        print('\r' + ' ' * 80, end='')
        colored_print(f"\r{SYMBOLS['error']} 流式输出异常: {e}", 'system_error')
        return None, None


def chat_loop(client: DoubaoClient, input_handler: InputHandler) -> None:
    """主聊天循环
    
    Args:
        client: 豆包客户端
        input_handler: 输入处理器
    """
    # 获取历史管理器
    history = get_chat_history(HISTORY_MAX_TURNS)
    
    while True:
        # 显示对话状态
        conv_length = client.get_conversation_length()
        status = f" (第{conv_length // 2 + 1}轮对话)" if conv_length > 0 else " (新对话)"
        
        # 获取用户输入
        user_input = input_handler.get_input(
            f"\n 您{status}: ",
            colored_print,
            SYMBOLS,
            COLORS,
            True
        )
        
        # 重新显示用户输入（确保格式一致）
        if user_input.strip():
            print(f"\033[1A\033[2K", end="")
            colored_print(f" 您{status}: {user_input}", 'user_text')
        
        # 检查输入是否为空
        if not user_input.strip():
            colored_print(f"{SYMBOLS['warning']}  没有收到你的文字哦，请输入有效的消息", 'system_warning')
            continue
        
        # 解析命令
        cmd_result = parse_command(user_input)
        
        # 处理退出命令
        if cmd_result['type'] == 'exit':
            colored_print(cmd_result['response'], 'system_info')
            break
        
        # 处理清空历史命令
        if cmd_result['type'] == 'clear':
            client.clear_history()
            colored_print(cmd_result['response'], 'system_success')
            # 保存清空命令到历史
            history.save_command('clear', '对话历史已清空')
            
            # 如果有消息内容，继续发送消息
            if cmd_result['message'].strip():
                # 修改命令类型为chat，继续处理
                cmd_result['type'] = 'chat'
            else:
                continue
        
        # 处理历史记录查看命令
        if cmd_result['type'] == 'history':
            display_history(cmd_result.get('history_turns', 10))
            continue
        
        # 处理错误命令
        if cmd_result['type'] == 'error':
            colored_print(cmd_result['response'], 'system_warning')
            continue
        
        # 处理聊天消息
        if cmd_result['type'] == 'chat':
            # 如果指定了target_response_id，则切换对话上下文
            if cmd_result['target_response_id']:
                target_id = cmd_result['target_response_id']
                
                # 验证短id是否存在于历史记录中
                from src.utils import get_id_mapper
                id_mapper = get_id_mapper()
                long_id = id_mapper.get_long_id(target_id)
                
                if not long_id:
                    colored_print(
                        f"{SYMBOLS['warning']} 未找到对应的聊天id ({target_id})，可能已从历史中删除",
                        'system_warning'
                    )
                    colored_print(
                        f"{SYMBOLS['info']} 使用 #history 命令查看可用的历史对话",
                        'system_info'
                    )
                    continue
                
                client.set_response_id(target_id)
                colored_print(
                    f"{SYMBOLS['success']} 已切换到对话 ({target_id}) 继续聊天",
                    'system_success'
                )
            
            # 处理AI响应
            print()
            short_id, bot_reply = process_ai_response(
                client,
                cmd_result['message'],
                cmd_result['thinking_mode'],
                cmd_result['thinking_status']
            )
            
            # 保存聊天记录到历史
            if short_id and bot_reply:
                # 获取长response_id
                from src.utils import get_id_mapper
                id_mapper = get_id_mapper()
                long_id = id_mapper.get_long_id(short_id)
                
                if long_id:
                    history.save_chat_turn(
                        short_id=short_id,
                        response_id=long_id,
                        user_message=cmd_result['message'],
                        bot_reply=bot_reply
                    )


def main() -> None:
    """主函数"""
    # 设置编码
    setup_encoding()
    
    # 初始化电池监控
    battery_monitor = get_battery_monitor()
    battery_monitor.start_display()
    
    # 显示欢迎界面
    print_welcome()
    print_usage()
    
    try:
        # 初始化豆包客户端
        client = DoubaoClient()
        colored_print(f"{SYMBOLS['success']} 豆包AI客户端初始化成功", 'system_success')
        
        # 初始化输入处理器
        input_handler = InputHandler()
        
        # 开始聊天循环
        chat_loop(client, input_handler)
        
    except ValueError as e:
        colored_print(f"{SYMBOLS['error']} 配置错误: {e}", 'system_error')
        colored_print(f"{SYMBOLS['docs']} 请检查 src/config.py 文件，确保已正确填写API密钥信息", 'system_info')
    except KeyboardInterrupt:
        colored_print(f"\n\n{SYMBOLS['goodbye']} 程序被用户中断，再见！", 'system_info')
    except Exception as e:
        colored_print(f"{SYMBOLS['error']} 程序运行异常: {e}", 'system_error')
    finally:
        battery_monitor.stop_display()
        battery_monitor.clear_display()


if __name__ == "__main__":
    main()

