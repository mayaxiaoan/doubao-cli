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
        
        # 简单地显示动画，让系统按默认规则处理光标
        current_msg = f'🤖 豆包: {spinners[idx]} {messages[msg_idx]}'
        print(f'\r{current_msg}', end='', flush=True)
        
        idx = (idx + 1) % len(spinners)
        msg_counter += 1
        time.sleep(0.1)  # 100ms刷新一次
    
    # 完全清除整行，避免遗留等待文字
    print('\r' + ' ' * 80, end='')  # 用空格完全覆盖可能的长文字
    print('\r🤖 豆包: ', end='', flush=True)


def main():
    """主函数"""
    print("=" * 50)
    print("🤖 豆包AI聊天程序")
    print("=" * 50)
    print("💡 输入消息开始聊天，输入 'exit' 或 'quit' 退出程序")
    print("💡 输入 'debug' 切换调试模式")
    print("=" * 50)
    
    # 调试模式标志
    debug_mode = False
    
    try:
        # 初始化豆包客户端
        client = DoubaoClient()
        print("✅ 豆包AI客户端初始化成功")
        
        # 开始聊天循环
        while True:
            # 获取用户输入
            user_input = input("\n👤 您: ").strip()
            
            # 检查退出命令
            if user_input.lower() in ['exit', 'quit', '退出', '再见']:
                print("👋 感谢使用豆包AI聊天程序，再见！")
                break
            
            # 检查调试模式切换
            if user_input.lower() == 'debug':
                debug_mode = not debug_mode
                status = "开启" if debug_mode else "关闭"
                print(f"🔧 调试模式已{status}")
                continue
            
            # 检查空输入
            if not user_input:
                print("⚠️  请输入有效的消息")
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
                # 添加一个计数器来跟踪接收到的chunk
                chunk_count = 0
                if debug_mode:
                    print(f"\n🔧 [调试] 开始接收流式数据...")
                
                for chunk in client.chat_stream(user_input):
                    chunk_count += 1
                    
                    if debug_mode:
                        print(f"\n🔧 [调试] 收到第{chunk_count}个chunk: '{chunk}' (长度:{len(chunk) if chunk else 0})")
                    
                    # 超时保护
                    if time.time() - start_time > timeout:
                        stop_animation.set()
                        time.sleep(0.15)  # 给动画线程时间完成清除操作
                        # 完全清除动画文字
                        print('\r' + ' ' * 80, end='')
                        print("\r⏰ 请求超时，正在尝试重新连接...")
                        break
                    
                    if chunk is not None and chunk:  # chunk不为None且不为空字符串
                        # 只有在收到真正的内容时才停止动画
                        if not first_chunk_received:
                            if debug_mode:
                                print(f"\n🔧 [调试] 停止动画，开始显示内容")
                            stop_animation.set()  # 停止动画
                            time.sleep(0.15)  # 给动画线程时间完成清除操作
                            first_chunk_received = True
                        
                        print(chunk, end="", flush=True)
                        response_chunks.append(chunk)
                
                # 确保动画已停止
                if not first_chunk_received:
                    stop_animation.set()
                    time.sleep(0.15)  # 给动画线程时间完成清除操作
                    # 完全清除动画文字
                    print('\r' + ' ' * 80, end='')
                    print('\r', end='', flush=True)
                    if debug_mode:
                        print(f"🔧 [调试] 没有收到任何有效内容，总共处理了{chunk_count}个chunk")
                
                # 换行准备下一轮对话
                if first_chunk_received:  # 只有收到内容时才换行
                    print()
                
                # 检查是否有完整回复
                if not response_chunks:
                    print("❌ 获取回复失败，请检查网络连接和API配置")
                elif debug_mode:
                    print(f"\n🔧 [调试] 成功接收{len(response_chunks)}个有效chunk，总计{chunk_count}个chunk")
                    
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
                print("🤖 豆包: ", end="", flush=True)
                response = client.chat(user_input)
                if response:
                    print(response)
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