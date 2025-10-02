# -*- coding: utf-8 -*-
"""
豆包AI聊天程序主入口
"""

import threading
import time
import sys
import os
from doubao_client import DoubaoClient
from config import SYMBOLS, COLORS, ENABLE_COLORS, DEFAULT_THINKING_MODE
from battery_monitor import battery_monitor


def setup_encoding():
    """设置编码环境"""
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        return True
    except Exception:
        return False


def fix_fbterm_encoding(text):
    """修复fbterm中文输入法导致的UTF-8编码问题"""
    if not text:
        return text
    
    try:
        # 检查是否包含无效的UTF-8序列
        text.encode('utf-8').decode('utf-8')
        return text
    except UnicodeDecodeError:
        # 使用替换策略修复截断的UTF-8字节序列
        fixed_text = text.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        return fixed_text


def smart_fix_utf8_sequence(text, error_msg):
    """智能修复UTF-8序列 - 基于错误信息进行精确修复"""
    import re
    
    # 解析错误信息，提取位置信息
    # 例如: "utf-8' codec can't decode byte 0xe5 in position 33: unexpected end of data"
    position_match = re.search(r'position (\d+)', error_msg)
    if not position_match:
        return text  # 无法解析位置信息，返回原文本
    
    error_position = int(position_match.group(1))
    
    # 将字符串转换为字节序列进行处理
    try:
        # 尝试将字符串编码为字节
        text_bytes = text.encode('latin-1')  # 使用latin-1确保不会丢失任何字节
    except:
        return text  # 如果无法编码，返回原文本
    
    # 检查错误位置是否在有效范围内
    if error_position >= len(text_bytes):
        return text
    
    # 尝试修复截断的UTF-8序列
    fixed_bytes = bytearray(text_bytes)
    
    # 从错误位置开始，尝试修复
    for i in range(error_position, len(fixed_bytes)):
        byte_val = fixed_bytes[i]
        
        # 检查是否是UTF-8多字节序列的开始
        if byte_val >= 0xC0:  # 2字节序列开始
            # 移除不完整的2字节序列
            fixed_bytes = fixed_bytes[:i]
            break
        elif byte_val >= 0xE0:  # 3字节序列开始
            # 移除不完整的3字节序列
            fixed_bytes = fixed_bytes[:i]
            break
        elif byte_val >= 0xF0:  # 4字节序列开始
            # 移除不完整的4字节序列
            fixed_bytes = fixed_bytes[:i]
            break
        elif byte_val >= 0x80:  # 多字节序列的延续字节
            # 移除不完整的延续字节
            fixed_bytes = fixed_bytes[:i]
            break
    
    # 将修复后的字节序列转换回字符串
    try:
        fixed_text = fixed_bytes.decode('utf-8', errors='replace')
        return fixed_text
    except:
        return text  # 如果修复失败，返回原文本


def waiting_animation(stop_event):
    """显示等待动画"""
    spinners = SYMBOLS['spinner']
    messages = ["正在连接豆包AI...", "正在思考中...", "正在组织语言...", "马上就好..."]
    
    idx = 0
    msg_idx = 0
    msg_counter = 0
    
    # 等待动画
    while not stop_event.is_set():
        if msg_counter > 0 and msg_counter % 30 == 0:
            msg_idx = (msg_idx + 1) % len(messages)
        
        current_msg = f'{SYMBOLS["bot"]} 豆包: {spinners[idx]} {messages[msg_idx]}'
        if ENABLE_COLORS:
            colored_msg = f'{COLORS["bot_text"]}{current_msg}{COLORS["reset"]}'
        else:
            colored_msg = current_msg
        print(f'\r{colored_msg}' + ' ' * 20, end='', flush=True)
        
        idx = (idx + 1) % len(spinners)
        msg_counter += 1
        time.sleep(0.1)
    
    print('\r' + ' ' * 80, end='')
    if ENABLE_COLORS:
        colored_prefix = f'{COLORS["bot_text"]}{SYMBOLS["bot"]} 豆包: {COLORS["reset"]}'
    else:
        colored_prefix = f'{SYMBOLS["bot"]} 豆包: '
    print(f'\r{colored_prefix}', end='', flush=True)


def colored_print(text, color_key='reset', end='\n', flush=False):
    """带颜色的安全打印函数"""
    if ENABLE_COLORS and color_key in COLORS:
        colored_text = f"{COLORS[color_key]}{text}{COLORS['reset']}"
    else:
        colored_text = text
    
    # 处理UTF-8编码问题
    try:
        print(colored_text, end=end, flush=flush)
    except UnicodeEncodeError:
        # 如果遇到编码错误，使用ASCII安全的方式
        try:
            safe_text = colored_text.encode('gbk', errors='replace').decode('gbk', errors='replace')
            print(safe_text, end=end, flush=flush)
        except:
            # 最后的备用方案：只保留ASCII字符
            ascii_text = ''.join(char if ord(char) < 128 else '?' for char in colored_text)
            print(ascii_text, end=end, flush=flush)


def colored_input(prompt, color_key='user_text'):
    """带颜色的安全输入函数 - 专门处理fbterm中文输入法问题"""
    if ENABLE_COLORS and color_key in COLORS:
        colored_prompt = f"{COLORS[color_key]}{prompt}{COLORS['reset']}"
    else:
        colored_prompt = prompt
    
    try:
        user_input = input(colored_prompt)
        
        # 专门处理fbterm中文输入法导致的UTF-8字节截断问题
        if isinstance(user_input, str):
            # 检查字符串是否包含无效的UTF-8序列
            try:
                # 尝试重新编码来检测无效序列
                user_input.encode('utf-8').decode('utf-8')
            except UnicodeDecodeError as e:
                # 捕获具体的错误信息进行精确修复
                error_msg = str(e)
                print(f"\n{SYMBOLS['warning']} 检测到输入编码问题: {error_msg}")
                
                # 尝试智能修复截断的UTF-8序列
                fixed_input = smart_fix_utf8_sequence(user_input, error_msg)
                if fixed_input != user_input:
                    print(f"{SYMBOLS['success']} 已自动修复编码问题")
                    user_input = fixed_input
                else:
                    # 如果智能修复失败，使用替换策略
                    user_input = user_input.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                    print(f"{SYMBOLS['warning']} 使用替换策略修复编码问题")
        
        elif isinstance(user_input, bytes):
            # 处理字节输入
            try:
                user_input = user_input.decode('utf-8')
            except UnicodeDecodeError as e:
                error_msg = str(e)
                print(f"\n{SYMBOLS['warning']} 检测到字节编码问题: {error_msg}")
                user_input = user_input.decode('utf-8', errors='replace')
                print(f"{SYMBOLS['success']} 已自动修复字节编码问题")
        
        return user_input.strip()
        
    except UnicodeDecodeError as e:
        print(f"\n{SYMBOLS['warning']} 输入编码错误: {e}")
        print(f"{SYMBOLS['info']} 这可能是fbterm中文输入法导致的，请重新输入")
        return ""
    except Exception as e:
        print(f"\n{SYMBOLS['warning']} 输入处理错误: {e}")
        print(f"{SYMBOLS['info']} 请重新输入")
        return ""


def main():
    """主函数"""
    setup_encoding()
    battery_monitor.start_display()
    
    # 显示欢迎界面
    colored_print(f"{SYMBOLS['separator']}" * 70, 'separator_line')
    colored_print(f"    {SYMBOLS['star']} 我是制杖但勤劳的豆包AI (支持上下文对话 + 深度思考控制) {SYMBOLS['star']}", 'bright_white')
    colored_print(f"{SYMBOLS['separator']}" * 70, 'separator_line')
    print()
    
    # ASCII艺术猫
    colored_print("      /\\_/\\    QUÉ MIRA BOBO?", 'cat_art')
    colored_print(" /\\  / o o \\    ﾉ", 'cat_art')
    colored_print("//\\\\ \\~(*)~/", 'cat_art')
    colored_print("`  \\/   ^ /", 'cat_art')
    colored_print("   | \\|| ||", 'cat_art')
    colored_print("   \\ '|| ||", 'cat_art')
    colored_print("    \\(()-())", 'cat_art')
    colored_print(" ~~~~~~~~~~~~~~~", 'cat_art')
    
    # 使用说明
    colored_print(f"{SYMBOLS['info']} 输入消息开始聊天", 'system_info')
    colored_print(f"{SYMBOLS['info']} 输入 'exit' 、'quit' 或 '退出' 关闭程序", 'system_info')
    colored_print(f"{SYMBOLS['info']} 输入 'clear'、'new' 或 '新话题' 开始新的聊天", 'system_info')
    colored_print(f"{SYMBOLS['info']} 深度思考控制：", 'system_info')
    colored_print("   - 默认：自动判断是否需要深度思考", 'system_info')
    colored_print("   - #think 开头：强制启用深度思考", 'system_info')
    colored_print("   - #fast 开头：禁用深度思考，快速回复", 'system_info')
    colored_print(f"{SYMBOLS['separator']}" * 70, 'separator_line')
    print()
    
    try:
        # 初始化豆包客户端
        client = DoubaoClient()
        colored_print(f"{SYMBOLS['success']} 豆包AI客户端初始化成功", 'system_success')
        
        # 开始聊天循环
        while True:
            # 显示对话状态
            conv_length = client.get_conversation_length()
            status = f" (第{conv_length // 2 + 1}轮对话)" if conv_length > 0 else " (新对话)"
            
            # 获取用户输入
            user_input = colored_input(f"\n{SYMBOLS['user']} 您{status}: ", 'user_text')
            
            # 修复fbterm中文输入法可能的编码问题
            user_input = fix_fbterm_encoding(user_input)
            
            # 重新显示用户输入
            if user_input.strip():
                print(f"\033[1A\033[2K", end="")
                colored_print(f"{SYMBOLS['user']} 您{status}: {user_input}", 'user_text')
            
            # 检查退出命令
            if user_input.lower() in ['exit', 'quit', '退出']:
                colored_print(f"{SYMBOLS['goodbye']} 感谢使用豆包AI聊天程序，再见！", 'system_info')
                battery_monitor.stop_display()
                break
            
            # 清空对话历史
            if user_input.lower() in ['clear', 'new', '新话题']:
                client.clear_history()
                colored_print(f"{SYMBOLS['success']} 对话历史已清空，我们可以开始新的聊天话题", 'system_success')
                continue
            
            # 检查用户输入是否为空
            if not user_input:
                colored_print(f"{SYMBOLS['warning']}  没有收到你的文字哦，请输入有效的消息", 'system_warning')
                continue
            
            # 解析深度思考控制符号
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
            
            #如果只有控制符号，实际内容为空，则给出提示
            if not actual_message.strip():
                colored_print(f"{SYMBOLS['warning']}  请在控制符号后输入有效的消息", 'system_warning')
                continue
            
            # 发送消息并获取流式回复
            print()
            
            # 启动等待动画
            stop_animation = threading.Event()
            animation_thread = threading.Thread(target=waiting_animation, args=(stop_animation,))
            animation_thread.daemon = True
            animation_thread.start()
            
            try:
                # 该变量用于标记是否已经打印过深度思考内容，主要用于控制输出格式，防止重复打印
                reasoning_displayed = False
                # 该变量用于标记是否已经打印过普通回复内容，主要用于控制输出格式，防止重复打印
                content_started = False
                # 该变量用于标记是否已经收到流式回复的第一个内容块（无论是reasoning还是content），
                # 主要用于停止等待动画和控制输出格式。
                first_chunk_received = False
                # 遍历流式回复
                for chunk_data in client.chat_stream(actual_message, thinking_mode):
                    if chunk_data is None:
                        continue
                    
                    # 处理深度思考内容
                    if chunk_data.get('type') == 'reasoning' and chunk_data.get('reasoning'):
                        if not reasoning_displayed:
                            if not first_chunk_received:
                                stop_animation.set()
                                time.sleep(0.15)
                                first_chunk_received = True
                            colored_print(f"\n{SYMBOLS['thinking']} 深度思考中...{thinking_status}", 'separator_line')
                            colored_print(f"{SYMBOLS['star']} {SYMBOLS['separator'] * 46} {SYMBOLS['star']}", 'separator_line')
                            reasoning_displayed = True
                        colored_print(chunk_data['reasoning'], 'bot_thinking', end="", flush=True)
                    
                    # 处理普通回复内容
                    elif chunk_data.get('type') == 'content' and chunk_data.get('content'):
                        if not content_started:
                            if reasoning_displayed:
                                colored_print(f"\n{SYMBOLS['star']} {SYMBOLS['separator'] * 46} {SYMBOLS['star']}", 'separator_line')
                                if thinking_status != " [要求深度思考]":
                                    colored_print(f"{SYMBOLS['bot']} 豆包{thinking_status}: ", 'bot_text', end="", flush=True)
                            elif not first_chunk_received:
                                stop_animation.set()
                                time.sleep(0.15)
                                first_chunk_received = True
                            content_started = True
                        
                        if not first_chunk_received:
                            stop_animation.set()
                            time.sleep(0.15)
                            first_chunk_received = True
                        
                        colored_print(chunk_data['content'], 'bot_text', end="", flush=True)
                
                # 确保动画已停止
                if not first_chunk_received:
                    stop_animation.set()
                    time.sleep(0.15)
                    print('\r' + ' ' * 80, end='')
                    print('\r', end='', flush=True)
                
                # 换行准备下一轮对话
                if first_chunk_received:
                    print()
                    
            except Exception as e:
                stop_animation.set()
                time.sleep(0.2)
                print('\r' + ' ' * 80, end='')
                colored_print(f"\r{SYMBOLS['error']} 流式输出异常: {e}", 'system_error')
    
    except ValueError as e:
        colored_print(f"{SYMBOLS['error']} 配置错误: {e}", 'system_error')
        colored_print(f"{SYMBOLS['docs']} 请检查config.py文件，确保已正确填写API密钥信息", 'system_info')
    except UnicodeDecodeError as e:
        colored_print(f"{SYMBOLS['error']} UTF-8编码错误: {e}", 'system_error')
        colored_print(f"{SYMBOLS['warning']} 程序将继续运行，但某些字符可能显示异常", 'system_warning')
    except KeyboardInterrupt:
        colored_print(f"\n\n{SYMBOLS['goodbye']} 程序被用户中断，再见！", 'system_info')
        battery_monitor.stop_display()
        battery_monitor.clear_display()
        sys.exit(0)
    except Exception as e:
        colored_print(f"{SYMBOLS['error']} 程序运行异常: {e}", 'system_error')


if __name__ == "__main__":
    main()