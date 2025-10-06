# -*- coding: utf-8 -*-
"""
豆包AI聊天程序主入口

使用方法：
    python main.py
"""

import sys
import threading

from src.client import DoubaoClient
from src.config import SYMBOLS, COLORS, DEFAULT_THINKING_MODE
from src.utils import setup_encoding, get_battery_monitor, InputHandler
from src.ui import (
    colored_print,
    print_welcome,
    print_usage,
    waiting_animation,
    StreamOutputHandler
)


def parse_command(user_input: str):
    """统一解析用户命令
    
    支持的命令格式：
        #think 消息内容          - 启用深度思考模式
        #fast 消息内容           - 快速回复模式
        #chat response_id 消息   - 从指定response_id继续对话
        #clear                   - 清空对话历史（也支持 #新话题）
        #exit                    - 退出程序（也支持 #退出, #quit）
        其他内容                 - 普通聊天消息
    
    Args:
        user_input: 用户输入
    
    Returns:
        dict: {
            'type': 命令类型 ('chat'/'exit'/'clear'),
            'message': 实际消息内容,
            'thinking_mode': 思考模式 ('enabled'/'disabled'/默认值),
            'thinking_status': 状态标记文本,
            'response': 命令响应消息（如果有）,
            'target_response_id': 目标response_id（如果有）
        }
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
        result['type'] = 'clear'
        result['response'] = f"{SYMBOLS['success']} 对话历史已清空，我们可以开始新的聊天话题"
        return result
    
    # 深度思考模式
    if command == 'think':
        result['type'] = 'chat'
        result['message'] = message
        result['thinking_mode'] = 'enabled'
        result['thinking_status'] = ' [要求深度思考]'
        return result
    
    # 快速回复模式
    if command == 'fast':
        result['type'] = 'chat'
        result['message'] = message
        result['thinking_mode'] = 'disabled'
        result['thinking_status'] = ' [快速回复]'
        return result
    
    # 从指定response_id继续对话
    if command in ['chat', 'continue', 'c', '对话']:
        # 解析格式：#chat response_id 消息内容（response_id可以是短id）
        chat_parts = message.split(' ', 1)
        if len(chat_parts) >= 1:
            target_response_id = chat_parts[0].strip()
            actual_message = chat_parts[1].strip() if len(chat_parts) > 1 else ''
            
            if target_response_id:
                result['type'] = 'chat'
                result['message'] = actual_message
                result['target_response_id'] = target_response_id
                result['thinking_status'] = f' [继续对话:{target_response_id}]'
                return result
        
        # 格式错误，提示用户
        result['type'] = 'error'
        result['response'] = f"{SYMBOLS['warning']} 命令格式错误！正确格式：#chat 短id 消息内容"
        return result
    
    # 未知命令，当作普通消息处理
    result['message'] = user_input
    return result


def process_ai_response(
    client: DoubaoClient,
    message: str,
    thinking_mode: str,
    thinking_status: str
) -> None:
    """处理AI流式响应
    
    Args:
        client: 豆包客户端
        message: 用户消息
        thinking_mode: 思考模式
        thinking_status: 思考状态标记
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
        
    except Exception as e:
        stop_animation.set()
        print('\r' + ' ' * 80, end='')
        colored_print(f"\r{SYMBOLS['error']} 流式输出异常: {e}", 'system_error')


def chat_loop(client: DoubaoClient, input_handler: InputHandler) -> None:
    """主聊天循环
    
    Args:
        client: 豆包客户端
        input_handler: 输入处理器
    """
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
        
        # 重新显示用户输入
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
            continue
        
        # 处理错误命令
        if cmd_result['type'] == 'error':
            colored_print(cmd_result['response'], 'system_warning')
            continue
        
        # 处理聊天消息
        if cmd_result['type'] == 'chat':
            # 检查消息内容是否为空
            if not cmd_result['message'].strip():
                colored_print(f"{SYMBOLS['warning']}  请在命令后输入有效的消息", 'system_warning')
                continue
            
            # 如果指定了target_response_id，则切换对话上下文
            if cmd_result['target_response_id']:
                target_id = cmd_result['target_response_id']
                client.set_response_id(target_id)
                colored_print(
                    f"{SYMBOLS['success']} 已切换到对话 [{target_id}] 继续聊天",
                    'system_success'
                )
            
            # 处理AI响应
            print()
            process_ai_response(
                client,
                cmd_result['message'],
                cmd_result['thinking_mode'],
                cmd_result['thinking_status']
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

