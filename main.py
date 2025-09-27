# -*- coding: utf-8 -*-
"""
豆包AI聊天程序主入口
简化版本，只实现基本聊天功能
"""

import threading
import time
import sys
from doubao_client import DoubaoClient


def waiting_animation(stop_event):
    """
    显示等待动画（跳动的点）
    
    Args:
        stop_event: 线程停止事件
    """
    # 使用旋转的动画字符，看起来更生动
    spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    messages = ["正在连接豆包AI...", "正在思考中...", "正在组织语言...", "马上就好..."]
    
    idx = 0
    msg_idx = 0
    msg_counter = 0
    
    while not stop_event.is_set():
        # 每30个周期（3秒）切换一次消息，但跳过第0次避免立即切换
        if msg_counter > 0 and msg_counter % 30 == 0:
            msg_idx = (msg_idx + 1) % len(messages)
        
        # 显示动画，每次都清除可能的残留文字
        current_msg = f'🤖 豆包: {spinners[idx]} {messages[msg_idx]}'
        print(f'\r{current_msg}' + ' ' * 20, end='', flush=True)  # 在消息后添加空格清除残留
        
        idx = (idx + 1) % len(spinners)
        msg_counter += 1
        time.sleep(0.1)  # 100ms刷新一次
    
    # 完全清除整行，避免遗留等待文字
    print('\r' + ' ' * 80, end='')  # 用空格完全覆盖可能的长文字
    print('\r🤖 豆包: ', end='', flush=True)


def main():
    """主函数"""
    print("=" * 70)
    print("🤖 豆包AI聊天程序 (支持上下文对话 + 深度思考控制)")
    print("=" * 70)
    print("💡 输入消息开始聊天")
    print("💡 输入 'exit' 或 'quit' 退出程序")
    print("💡 输入 'clear' 清空对话历史")
    print("💡 深度思考控制：")
    print("   - 默认：自动判断是否需要深度思考")
    print("   - #think 开头：强制启用深度思考")
    print("   - #fast 开头：禁用深度思考，快速回复")
    print("=" * 70)
    
    try:
        # 初始化豆包客户端
        client = DoubaoClient()
        print("✅ 豆包AI客户端初始化成功")
        
        # 开始聊天循环
        while True:
            # 显示对话状态
            conv_length = client.get_conversation_length()
            if conv_length > 0:
                status = f" (第{conv_length // 2 + 1}轮对话)"
            else:
                status = " (新对话)"
            
            # 获取用户输入
            user_input = input(f"\n👤 您{status}: ").strip()
            
            # 检查退出命令
            if user_input.lower() in ['exit', 'quit', '退出', '再见']:
                print("👋 感谢使用豆包AI聊天程序，再见！")
                break
            
            # 检查清空历史命令
            if user_input.lower() in ['clear', '清空', 'reset']:
                client.clear_history()
                print("✅ 对话历史已清空")
                continue
            
            # 检查空输入
            if not user_input:
                print("⚠️  请输入有效的消息")
                continue
            
            # 解析深度思考控制符号
            thinking_mode = "auto"  # 默认自动判断
            actual_message = user_input  # 实际发送的消息
            thinking_status = ""  # 显示给用户的状态
            
            if user_input.startswith("#think "):
                thinking_mode = "enabled"
                actual_message = user_input[7:]  # 去掉 "#think " 前缀
                thinking_status = " [强制深度思考]"
            elif user_input.startswith("#fast "):
                thinking_mode = "disabled"
                actual_message = user_input[6:]  # 去掉 "#fast " 前缀
                thinking_status = " [快速回复]"
            
            # 检查处理后的消息是否为空
            if not actual_message.strip():
                print("⚠️  请在控制符号后输入有效的消息")
                continue
            
            # 发送消息并获取流式回复
            # 确保在新行开始显示动画，避免与用户输入重合
            print()  # 换行，将动画显示在新行
            
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
                        print("\r⏰ 请求超时，正在尝试重新连接...")
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
                            print(f"\n💭 深度思考中...{thinking_status}")
                            print("-" * 50)
                            reasoning_displayed = True
                        print(chunk_data['reasoning'], end="", flush=True)
                        response_chunks.append(chunk_data['reasoning'])
                    
                    # 处理普通回复内容
                    elif chunk_data.get('type') == 'content' and chunk_data.get('content'):
                        # 只有在第一次显示回复内容时才显示前缀
                        if not content_started:
                            if reasoning_displayed:
                                # 如果之前显示过深度思考，现在开始显示回复
                                print("\n" + "-" * 50)
                                print(f"🤖 豆包{thinking_status}: ", end="", flush=True)
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
                        
                        print(chunk_data['content'], end="", flush=True)
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
                    print("❌ 获取回复失败，请检查网络连接和API配置")
                    
            except Exception as e:
                # 停止动画
                stop_animation.set()
                # 给动画线程一点时间停止
                time.sleep(0.2)
                
                # 完全清除动画文字
                print('\r' + ' ' * 80, end='')
                print(f"\r❌ 流式输出异常: {e}")
                print("💡 尝试使用非流式模式...")
                
                # 回退到非流式模式
                print(f"🤖 豆包{thinking_status}: ", end="", flush=True)
                response_data = client.chat(actual_message, thinking_mode)
                if response_data and response_data.get('content'):
                    # 先显示深度思考（如果有）
                    if response_data.get('is_reasoning') and response_data.get('reasoning'):
                        print(f"\n💭 深度思考内容{thinking_status}:")
                        print("-" * 50)
                        print(response_data['reasoning'])
                        print("-" * 50)
                        print(f"🤖 豆包{thinking_status}: ", end="")
                    
                    print(response_data['content'])
                else:
                    print("❌ 获取回复失败，请检查网络连接和API配置")
    
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print("📝 请检查config.py文件，确保已正确填写API密钥信息")
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断，再见！")
        # 确保所有线程正常退出
        sys.exit(0)
    except Exception as e:
        print(f"❌ 程序运行异常: {e}")


if __name__ == "__main__":
    main()