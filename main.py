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
    """带颜色的安全输入函数"""
    if ENABLE_COLORS and color_key in COLORS:
        colored_prompt = f"{COLORS[color_key]}{prompt}{COLORS['reset']}"
    else:
        colored_prompt = prompt
    
    # 先打印提示符
    print(colored_prompt, end='', flush=True)
    
    # 存储用户实际输入的原始字节数据
    raw_input = None
    displayed_input = None
    
    try:
        # 尝试从stdin.buffer读取原始字节
        if hasattr(sys.stdin, 'buffer'):
            raw_input = sys.stdin.buffer.readline()
            # 尝试解码
            user_input = raw_input.decode('utf-8').rstrip('\n\r')
            return user_input.strip()
        else:
            # 如果没有buffer属性，使用常规方式
            user_input = sys.stdin.readline().rstrip('\n\r')
            return user_input.strip()
    except UnicodeDecodeError as e:
        # 当发生编码错误时，我们有原始字节数据
        print(f"\033[1A\033[2K", end="")  # 向上一行并清除
        
        # 尝试用不同的方式显示原始输入
        displayed_input = None
        cleaned_input = None
        
        if raw_input:
            try:
                # 使用replace错误处理策略，用�替换无法解码的字符
                displayed_input = raw_input.decode('utf-8', errors='replace').rstrip('\n\r')
                # 创建清理后的版本，移除所有替换字符（�）
                cleaned_input = displayed_input.replace('\ufffd', '').strip()
            except:
                try:
                    # 尝试GBK编码
                    displayed_input = raw_input.decode('gbk', errors='replace').rstrip('\n\r')
                    cleaned_input = displayed_input.replace('\ufffd', '').strip()
                except:
                    displayed_input = None
                    cleaned_input = None
        
        # 用红色重新显示提示符和用户输入
        if displayed_input:
            colored_print(f"{prompt}{displayed_input}", 'system_error')
        else:
            colored_print(f"{prompt}[编码错误，输入内容无法显示]", 'system_error')
        
        colored_print(f"\n{SYMBOLS['warning']} 输入编码错误: {e}", 'system_error')
        colored_print(f"{SYMBOLS['info']} 这可能是删除汉字导致的，由于编码显示的问题，你每删除一个汉字实际要按三次回退键哦，记住次数，不要在意显示被删除的文字", 'system_warning')
        
        # 如果成功清理出有效内容，询问用户是否使用清理后的内容
        if cleaned_input:
            colored_print(f"\n{SYMBOLS['info']} 已自动清理错误字符，处理后的内容为:", 'system_info')
            colored_print(f"{SYMBOLS['user']} {cleaned_input}", 'bright_green')
            colored_print(f"{SYMBOLS['info']} 是否使用清理后的内容发送？(y/n): ", 'system_info', end='', flush=True)
            
            try:
                choice = input().strip().lower()
                if choice in ['y', 'yes', '是', '']:
                    colored_print(f"{SYMBOLS['success']} 使用清理后的内容继续", 'system_success')
                    return cleaned_input
                else:
                    colored_print(f"{SYMBOLS['info']} 已取消，请重新输入", 'system_info')
            except:
                pass
        
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