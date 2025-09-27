# -*- coding: utf-8 -*-
"""
豆包AI聊天程序主入口
简化版本，只实现基本聊天功能
"""

from doubao_client import DoubaoClient


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
            
            # 发送消息并获取回复
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
    except Exception as e:
        print(f"❌ 程序运行异常: {e}")


if __name__ == "__main__":
    main()