# -*- coding: utf-8 -*-
"""
豆包AI聊天程序主入口
简化版本，只实现基本聊天功能
"""

import threading
import time
import sys
import os
import locale
from doubao_client import DoubaoClient
from config import SYMBOLS, COLORS, ENABLE_COLORS, DEFAULT_THINKING_MODE
from battery_monitor import battery_monitor


def setup_encoding():
    """设置编码环境，解决Linux下的UTF-8问题"""
    try:
        # 设置Python默认编码
        if hasattr(sys, 'setdefaultencoding'):
            sys.setdefaultencoding('utf-8')
        
        # 强制设置stdout和stderr的编码
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        
        # 设置locale
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            except locale.Error:
                pass  # 忽略locale设置失败
        
        # 设置环境变量
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        return True
    except Exception as e:
        print(f"{SYMBOLS['warning']} 编码环境设置警告: {e}")
        return False


def waiting_animation(stop_event):
    """
    显示等待动画（跳动的点）
    
    Args:
        stop_event: 线程停止事件
    """
    # 使用旋转的动画字符，看起来更生动
    spinners = SYMBOLS['spinner']
    messages = ["正在连接豆包AI...", "正在思考中...", "正在组织语言...", "马上就好..."]
    
    idx = 0
    msg_idx = 0
    msg_counter = 0
    
    while not stop_event.is_set():
        # 每30个周期（3秒）切换一次消息，但跳过第0次避免立即切换
        if msg_counter > 0 and msg_counter % 30 == 0:
            msg_idx = (msg_idx + 1) % len(messages)
        
        # 显示动画，每次都清除可能的残留文字
        current_msg = f'{SYMBOLS["bot"]} 豆包: {spinners[idx]} {messages[msg_idx]}'
        if ENABLE_COLORS:
            colored_msg = f'{COLORS["bot_text"]}{current_msg}{COLORS["reset"]}'
        else:
            colored_msg = current_msg
        print(f'\r{colored_msg}' + ' ' * 20, end='', flush=True)  # 在消息后添加空格清除残留
        
        idx = (idx + 1) % len(spinners)
        msg_counter += 1
        time.sleep(0.1)  # 100ms刷新一次
    
    # 完全清除整行，避免遗留等待文字
    print('\r' + ' ' * 80, end='')  # 用空格完全覆盖可能的长文字
    if ENABLE_COLORS:
        colored_prefix = f'{COLORS["bot_text"]}{SYMBOLS["bot"]} 豆包: {COLORS["reset"]}'
    else:
        colored_prefix = f'{SYMBOLS["bot"]} 豆包: '
    print(f'\r{colored_prefix}', end='', flush=True)


def safe_input(prompt):
    """安全的输入函数，处理编码问题"""
    try:
        user_input = input(prompt)
        # 确保输入是UTF-8编码的字符串
        if isinstance(user_input, bytes):
            user_input = user_input.decode('utf-8', errors='replace')
        elif isinstance(user_input, str):
            # 重新编码确保没有问题
            user_input = user_input.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        return user_input.strip()
    except UnicodeDecodeError as e:
        print(f"{SYMBOLS['warning']} 输入编码错误: {e}")
        return ""
    except Exception as e:
        print(f"{SYMBOLS['warning']} 输入处理错误: {e}")
        return ""


def safe_print(text, end='\n', flush=False):
    """安全的打印函数，处理编码问题"""
    try:
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')
        print(text, end=end, flush=flush)
    except UnicodeEncodeError as e:
        # 如果仍有编码问题，使用ASCII模式
        safe_text = text.encode('ascii', errors='replace').decode('ascii')
        print(safe_text, end=end, flush=flush)
        print(f"{SYMBOLS['warning']} 字符编码问题已处理: {e}")
    except Exception as e:
        print(f"输出错误: {e}", end=end, flush=flush)


def colored_print(text, color_key='reset', end='\n', flush=False):
    """带颜色的安全打印函数"""
    if ENABLE_COLORS and color_key in COLORS:
        colored_text = f"{COLORS[color_key]}{text}{COLORS['reset']}"
    else:
        colored_text = text
    safe_print(colored_text, end=end, flush=flush)


def colored_input(prompt, color_key='user_text'):
    """带颜色的安全输入函数"""
    if ENABLE_COLORS and color_key in COLORS:
        colored_prompt = f"{COLORS[color_key]}{prompt}{COLORS['reset']}"
    else:
        colored_prompt = prompt
    return safe_input(colored_prompt)


def main():
    """主函数"""
    # 首先设置编码环境
    encoding_ok = setup_encoding()
    
    # 启动电池监控显示
    battery_monitor.start_display()
    
    colored_print(f"{SYMBOLS['separator']}" * 70, 'separator_line')
    colored_print(f"    {SYMBOLS['star']} 我是制杖但勤劳的豆包AI (支持上下文对话 + 深度思考控制) {SYMBOLS['star']}", 'bright_white')
    colored_print(f"{SYMBOLS['separator']}" * 70, 'separator_line')
    print()  # 添加一个空行使界面更清晰
    # 显示可爱的ASCII艺术猫
    colored_print("      /\\_/\\    QUÉ MIRA BOBO?", 'cat_art')
    colored_print(" /\\  / o o \\    ﾉ", 'cat_art')
    colored_print("//\\\\ \\~(*)~/", 'cat_art')
    colored_print("`  \\/   ^ /", 'cat_art')
    colored_print("   | \\|| ||", 'cat_art')
    colored_print("   \\ '|| ||", 'cat_art')
    colored_print("    \\(()-())", 'cat_art')
    colored_print(" ~~~~~~~~~~~~~~~", 'cat_art') 
    colored_print(f"{SYMBOLS['info']} 输入消息开始聊天", 'system_info')
    colored_print(f"{SYMBOLS['info']} 输入 'exit' 、'quit' 或 '退出' 关闭程序", 'system_info')
    colored_print(f"{SYMBOLS['info']} 输入 'clear'、'new' 或 '新话题' 开始新的聊天", 'system_info')
    #colored_print(f"{SYMBOLS['info']} 输入 'health'、'status' 或 '健康' 检查连接状态", 'system_info')#该命令为隐藏命令，不需要暴露给用户
    colored_print(f"{SYMBOLS['info']} 深度思考控制：", 'system_info')
    colored_print("   - 默认：自动判断是否需要深度思考", 'system_info')
    colored_print("   - #think 开头：强制启用深度思考", 'system_info')
    colored_print("   - #fast 开头：禁用深度思考，快速回复", 'system_info')
    colored_print(f"{SYMBOLS['separator']}" * 70, 'separator_line')
    print()  # 添加一个空行
    
    try:
        # 初始化豆包客户端
        client = DoubaoClient()
        colored_print(f"{SYMBOLS['success']} 豆包AI客户端初始化成功", 'system_success')
        
        # 开始聊天循环
        while True:
            # 显示对话状态
            conv_length = client.get_conversation_length()
            if conv_length > 0:
                status = f" (第{conv_length // 2 + 1}轮对话)"
            else:
                status = " (新对话)"
            
            # 获取用户输入（使用安全输入函数）
            user_input = colored_input(f"\n{SYMBOLS['user']} 您{status}: ", 'user_text')
            
            # 用户输入提示显示完成后，再显示电池信息
            battery_monitor.refresh_now()
            
            # 用绿色重新显示用户输入的完整内容（覆盖白色输入）
            if user_input.strip():  # 只有非空输入才重新显示
                # 清除上一行并重新以绿色显示
                print(f"\033[1A\033[2K", end="")  # 向上一行并清除整行
                colored_print(f"{SYMBOLS['user']} 您{status}: {user_input}", 'user_text')
            
            # 检查退出命令
            if user_input.lower() in ['exit', 'quit', '退出']:
                colored_print(f"{SYMBOLS['goodbye']} 感谢使用豆包AI聊天程序，再见！", 'system_info')
                # 停止电池监控
                battery_monitor.stop_display()
                battery_monitor.clear_display()
                break
            
            # 检查清空历史命令
            if user_input.lower() in ['clear', 'new','新话题']:
                client.clear_history()
                colored_print(f"{SYMBOLS['success']} 对话历史已清空，我们可以开始新的聊天话题", 'system_success')
                continue
            
            
            # 检查健康状态命令
            if user_input.lower() in ['health', 'status', '健康', '状态']:
                health_info = client.health_check()
                if health_info['status'] == 'healthy':
                    colored_print(f"{SYMBOLS['success']} 连接状态: {health_info['message']} (响应时间: {health_info['response_time']}秒)", 'system_success')
                else:
                    colored_print(f"{SYMBOLS['error']} 连接状态: {health_info['message']}", 'system_error')
                continue
            
            
            # 检查空输入
            if not user_input:
                colored_print(f"{SYMBOLS['warning']}  没有收到你的文字哦，请输入有效的消息", 'system_warning')
                continue
            
            # 解析深度思考控制符号
            thinking_mode = DEFAULT_THINKING_MODE  # 使用配置的默认模式
            actual_message = user_input  # 实际发送的消息
            thinking_status = ""  # 显示给用户的状态
            
            if user_input.startswith("#think "):
                thinking_mode = "enabled"
                actual_message = user_input[7:]  # 去掉 "#think " 前缀
                thinking_status = " [要求深度思考]"
            elif user_input.startswith("#fast "):
                thinking_mode = "disabled"
                actual_message = user_input[6:]  # 去掉 "#fast " 前缀
                thinking_status = " [快速回复]"
            
            # 检查处理后的消息是否为空
            if not actual_message.strip():
                colored_print(f"{SYMBOLS['warning']}  请在控制符号后输入有效的消息", 'system_warning')
                continue
            
            # 发送消息并获取流式回复
            # 确保在新行开始显示动画，避免与用户输入重合
            print()  # 换行，将动画显示在新行
            
            # 豆包开始流式传输时隐藏电池显示
            battery_monitor.hide_display()
            
            # 启动等待动画
            stop_animation = threading.Event()
            animation_thread = threading.Thread(target=waiting_animation, args=(stop_animation,))
            animation_thread.daemon = True  # 设置为守护线程
            animation_thread.start()
            
            # 记录开始时间，用于超时保护
            start_time = time.time()
            timeout = 30  # 30秒超时
            
            # 使用流式输出逐字显示回复
            response_chunks = []
            first_chunk_received = False
            
            try:
                reasoning_displayed = False  # 是否已显示过深度思考
                content_started = False      # 是否已开始显示正式回复
                
                for chunk_data in client.chat_stream(actual_message, thinking_mode):
                    # 超时保护
                    if time.time() - start_time > timeout:
                        stop_animation.set()
                        time.sleep(0.15)  # 给动画线程时间完成清除操作
                        # 完全清除动画文字
                        print('\r' + ' ' * 80, end='')
                        colored_print(f"\r{SYMBOLS['timeout']} 请求超时，正在尝试重新连接...", 'system_warning')
                        break
                    
                    if chunk_data is None:
                        continue
                    
                    # 处理深度思考内容
                    if chunk_data.get('type') == 'reasoning' and chunk_data.get('reasoning'):
                        if not reasoning_displayed:
                            # 第一次显示深度思考时，先停止动画并显示标题
                            if not first_chunk_received:
                                stop_animation.set()
                                time.sleep(0.15)
                                first_chunk_received = True
                            colored_print(f"\n{SYMBOLS['thinking']} 深度思考中...{thinking_status}", 'bot_thinking')
                            colored_print(f"{SYMBOLS['star']} {SYMBOLS['separator'] * 46} {SYMBOLS['star']}", 'separator_line')
                            reasoning_displayed = True
                        colored_print(chunk_data['reasoning'], 'bot_thinking', end="", flush=True)
                        response_chunks.append(chunk_data['reasoning'])
                    
                    # 处理普通回复内容
                    elif chunk_data.get('type') == 'content' and chunk_data.get('content'):
                        # 只有在第一次显示回复内容时才显示前缀
                        if not content_started:
                            if reasoning_displayed:
                                # 如果之前显示过深度思考，现在开始显示回复
                                colored_print(f"\n{SYMBOLS['star']} {SYMBOLS['separator'] * 46} {SYMBOLS['star']}", 'separator_line')
                                # 强制思考后不显示豆包标题和思考状态，直接显示内容
                                if thinking_status == " [要求深度思考]":
                                    # 不显示任何前缀，直接开始显示内容
                                    pass
                                else:
                                    colored_print(f"{SYMBOLS['bot']} 豆包{thinking_status}: ", 'bot_text', end="", flush=True)
                            elif not first_chunk_received:
                                # 如果没有深度思考，直接开始显示回复（动画会自动清除前缀）
                                stop_animation.set()  # 停止动画
                                time.sleep(0.15)  # 给动画线程时间完成清除操作
                                first_chunk_received = True
                            content_started = True
                        
                        # 只有在收到真正的内容时才停止动画
                        if not first_chunk_received:
                            stop_animation.set()  # 停止动画
                            time.sleep(0.15)  # 给动画线程时间完成清除操作
                            first_chunk_received = True
                        
                        colored_print(chunk_data['content'], 'bot_text', end="", flush=True)
                        response_chunks.append(chunk_data['content'])
                
                # 确保动画已停止
                if not first_chunk_received:
                    stop_animation.set()
                    time.sleep(0.15)  # 给动画线程时间完成清除操作
                    # 完全清除动画文字
                    print('\r' + ' ' * 80, end='')
                    print('\r', end='', flush=True)
                
                # 换行准备下一轮对话
                if first_chunk_received:  # 只有收到内容时才换行
                    print()
                
                # 检查是否有完整回复
                if not response_chunks:
                    colored_print(f"{SYMBOLS['error']} 获取回复失败，请检查网络连接和API配置", 'system_error')
                    
            except Exception as e:
                # 停止动画
                stop_animation.set()
                # 给动画线程一点时间停止
                time.sleep(0.2)
                
                # 完全清除动画文字
                print('\r' + ' ' * 80, end='')
                colored_print(f"\r{SYMBOLS['error']} 流式输出异常: {e}", 'system_error')
                colored_print(f"{SYMBOLS['error']} 获取回复失败，请检查网络连接和API配置", 'system_error')
    
    except ValueError as e:
        colored_print(f"{SYMBOLS['error']} 配置错误: {e}", 'system_error')
        colored_print(f"{SYMBOLS['docs']} 请检查config.py文件，确保已正确填写API密钥信息", 'system_info')
    except KeyboardInterrupt:
        colored_print(f"\n\n{SYMBOLS['goodbye']} 程序被用户中断，再见！", 'system_info')
        # 停止电池监控
        battery_monitor.stop_display()
        battery_monitor.clear_display()
        # 确保所有线程正常退出
        sys.exit(0)
    except Exception as e:
        colored_print(f"{SYMBOLS['error']} 程序运行异常: {e}", 'system_error')


if __name__ == "__main__":
    main()