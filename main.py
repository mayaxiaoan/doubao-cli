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
        # 每30个周期（3秒）切换一次消息
        if msg_counter % 30 == 0:
            msg_idx = (msg_idx + 1) % len(messages)
        
        # 清除当前行并显示动画
        sys.stdout.write(f'\r🤖 豆包: {spinners[idx]} {messages[msg_idx]}')
        sys.stdout.flush()
        
        idx = (idx + 1) % len(spinners)
        msg_counter += 1
        time.sleep(0.1)  # 100ms刷新一次
    
    # 清除等待动画行，准备显示实际内容
    sys.stdout.write('\r🤖 豆包: ')
    sys.stdout.flush()


def main():
    """主函数"""
    print("=" * 50)
    print("🤖 豆包AI聊天程序")
    print("=" * 50)
    print("💡 输入消息开始聊天，输入 'exit' 或 'quit' 退出程序")
    print("=" * 50)
    
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
            
            # 检查空输入
            if not user_input:
                print("⚠️  请输入有效的消息")
                continue
            
            # 发送消息并获取流式回复
            # 启动等待动画
            stop_animation = threading.Event()
            animation_thread = threading.Thread(target=waiting_animation, args=(stop_animation,))
            animation_thread.daemon = True  # 设置为守护线程
            animation_thread.start()
            
            # 使用流式输出逐字显示回复
            response_chunks = []
            first_chunk_received = False
            
            try:
                for chunk in client.chat_stream(user_input):
                    if chunk is not None:
                        # 如果是第一个数据块，停止动画
                        if not first_chunk_received:
                            stop_animation.set()  # 停止动画
                            first_chunk_received = True
                        
                        print(chunk, end="", flush=True)
                        response_chunks.append(chunk)
                
                # 确保动画已停止
                if not first_chunk_received:
                    stop_animation.set()
                
                # 换行准备下一轮对话
                print()
                
                # 检查是否有完整回复
                if not response_chunks:
                    print("❌ 获取回复失败，请检查网络连接和API配置")
                    
            except Exception as e:
                # 停止动画
                stop_animation.set()
                
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