# -*- coding: utf-8 -*-
"""
豆包 AI 聊天程序主入口

这是一个基于火山引擎豆包 AI 的命令行聊天应用，提供：
- 上下文对话管理
- 深度思考模式
- 联网搜索
- 历史记录管理
- 短 ID 快速切换对话

使用方法：
    python main.py
"""

import sys
import threading
from typing import Optional, Tuple

import src.config as config
from src.client import DoubaoClient
from src.command_handler import parse_command
from src.config import COLORS, HISTORY_MAX_TURNS, SYMBOLS
from src.key_manager import get_key_manager
from src.ui import (
    StreamOutputHandler,
    colored_print,
    print_usage,
    print_welcome,
    waiting_animation,
)
from src.utils import (
    InputHandler,
    get_battery_monitor,
    get_chat_history,
    get_id_mapper,
    setup_encoding,
)




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
) -> Tuple[Optional[str], Optional[str]]:
    """处理 AI 流式响应
    
    Args:
        client: 豆包客户端
        message: 用户消息
        thinking_mode: 思考模式（'auto', 'enabled', 'disabled'）
        thinking_status: 思考状态标记文本
    
    Returns:
        (short_id, bot_reply): 短 ID 和 AI 回复内容（不含思考部分）
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


def chat_loop(
    client: DoubaoClient,
    input_handler: InputHandler,
    battery_monitor
) -> None:
    """主聊天循环
    
    处理用户输入、命令解析、AI 响应等主要逻辑。
    
    Args:
        client: 豆包客户端实例
        input_handler: 输入处理器实例
        battery_monitor: 电池监控器实例
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
        
        # 记录用户活动时间（用于电池自适应刷新）
        battery_monitor.update_user_activity()
        
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
        
        # 处理删除历史记录命令
        if cmd_result['type'] == 'hdel':
            delete_turns = cmd_result.get('delete_turns', 0)
            deleted_count = history.delete_recent_turns(delete_turns)
            
            if deleted_count > 0:
                colored_print(
                    f"{SYMBOLS['success']} 已成功删除最近 {deleted_count} 轮历史记录",
                    'system_success'
                )
                # 如果删除了所有记录，清空客户端对话历史
                if history.get_total_turns() == 0:
                    client.clear_history()
                    colored_print(
                        f"{SYMBOLS['info']} 已清空所有历史记录和对话上下文",
                        'system_info'
                    )
            else:
                colored_print(
                    f"{SYMBOLS['info']} 没有历史记录可删除",
                    'system_info'
                )
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
                id_mapper = get_id_mapper()
                long_id = id_mapper.get_long_id(short_id)
                
                if long_id:
                    history.save_chat_turn(
                        short_id=short_id,
                        response_id=long_id,
                        user_message=cmd_result['message'],
                        bot_reply=bot_reply
                    )
            elif not short_id or not bot_reply:
                # AI 响应失败的情况
                colored_print(
                    f"{SYMBOLS['error']} AI 响应失败，请重试",
                    'system_error'
                )


def initialize_api_keys() -> bool:
    """初始化 API 密钥
    
    检查并加载 API 密钥，如果不存在则引导用户输入。
    
    Returns:
        初始化成功返回 True，失败返回 False
    """
    key_manager = get_key_manager()
    
    # 检查密钥文件是否存在
    if not key_manager.key_file_exists():
        # 首次运行，提示用户输入密钥
        if not key_manager.prompt_for_keys():
            return False
    else:
        # 加载现有密钥
        if not key_manager.load_keys():
            colored_print(
                f"{SYMBOLS['error']} 读取密钥文件失败！",
                'system_error'
            )
            colored_print(
                f"{SYMBOLS['info']} 请检查 {key_manager.key_file} 文件格式是否正确",
                'system_info'
            )
            return False
    
    # 验证密钥
    if not key_manager.validate_keys():
        colored_print(
            f"{SYMBOLS['error']} API 密钥格式不正确！",
            'system_error'
        )
        colored_print(
            f"{SYMBOLS['info']} 请检查 {key_manager.key_file} 文件中的密钥",
            'system_info'
        )
        return False
    
    # 将密钥设置到配置中
    api_key, endpoint_id = key_manager.get_keys()
    if api_key and endpoint_id:
        config.ARK_API_KEY = api_key
        config.ARK_ENDPOINT_ID = endpoint_id
    else:
        return False
    
    return True


def main() -> None:
    """主函数 - 程序入口
    
    初始化所有组件并启动主聊天循环。
    """
    # 设置终端编码
    setup_encoding()
    
    # 初始化 API 密钥
    if not initialize_api_keys():
        print("\n程序无法启动，请配置正确的 API 密钥后重试。")
        return
    
    # 初始化电池监控（仅 Linux TTY 模式有效）
    battery_monitor = get_battery_monitor()
    battery_monitor.start_display()
    
    # 显示欢迎界面和使用说明
    print_welcome()
    print_usage()
    
    try:
        # 初始化豆包 AI 客户端
        client = DoubaoClient()
        colored_print(
            f"{SYMBOLS['success']} 豆包 AI 客户端初始化成功",
            'system_success'
        )
        
        # 初始化输入处理器
        input_handler = InputHandler()
        
        # 进入主聊天循环
        chat_loop(client, input_handler, battery_monitor)
        
    except ValueError as e:
        colored_print(f"{SYMBOLS['error']} 配置错误: {e}", 'system_error')
        colored_print(
            f"{SYMBOLS['docs']} 请检查 api_keys.ini 中的密钥是否正确",
            'system_info'
        )
    except KeyboardInterrupt:
        colored_print(
            f"\n\n{SYMBOLS['goodbye']} 程序被用户中断，再见！",
            'system_info'
        )
    except Exception as e:
        colored_print(f"{SYMBOLS['error']} 程序运行异常: {e}", 'system_error')
    finally:
        # 清理电池监控显示
        battery_monitor.stop_display()
        battery_monitor.clear_display()


if __name__ == "__main__":
    main()

