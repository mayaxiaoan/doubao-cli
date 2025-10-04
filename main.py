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


def parse_thinking_mode(user_input: str):
    """解析深度思考控制符号
    
    Args:
        user_input: 用户输入
    
    Returns:
        tuple: (thinking_mode, actual_message, thinking_status)
    """
    thinking_mode = DEFAULT_THINKING_MODE
    actual_message = user_input
    thinking_status = ""
    
    if user_input.startswith("#think "):
        thinking_mode = "enabled"
        actual_message = user_input[7:]
        thinking_status = " [要求深度思考]"
    elif user_input.startswith("#fast "):
        thinking_mode = "disabled"
        actual_message = user_input[6:]
        thinking_status = " [快速回复]"
    
    return thinking_mode, actual_message, thinking_status


def handle_user_command(user_input: str, client: DoubaoClient) -> bool:
    """处理用户命令
    
    Args:
        user_input: 用户输入
        client: 豆包客户端
    
    Returns:
        如果是退出命令返回True，否则返回False
    """
    # 检查退出命令
    if user_input.lower() in ['exit', 'quit', '退出']:
        colored_print(f"{SYMBOLS['goodbye']} 感谢使用豆包AI聊天程序，再见！", 'system_info')
        return True
    
    # 清空对话历史
    if user_input.lower() in ['clear', 'new', '新话题']:
        client.clear_history()
        colored_print(f"{SYMBOLS['success']} 对话历史已清空，我们可以开始新的聊天话题", 'system_success')
    
    return False


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
        
        # 处理命令
        if handle_user_command(user_input, client):
            break
        
        # 检查输入是否为空
        if not user_input:
            colored_print(f"{SYMBOLS['warning']}  没有收到你的文字哦，请输入有效的消息", 'system_warning')
            continue
        
        # 解析深度思考控制符号
        thinking_mode, actual_message, thinking_status = parse_thinking_mode(user_input)
        
        # 如果只有控制符号，实际内容为空
        if not actual_message.strip():
            colored_print(f"{SYMBOLS['warning']}  请在控制符号后输入有效的消息", 'system_warning')
            continue
        
        # 处理AI响应
        print()
        process_ai_response(client, actual_message, thinking_mode, thinking_status)


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

