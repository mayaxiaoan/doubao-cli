#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTY穿透测试脚本
用于验证是否可以直接在TTY设备上显示信息并穿透fbterm
"""

import os
import sys
import time

def test_tty_penetration():
    """测试TTY穿透功能"""
    print("=== TTY穿透测试 ===")
    
    # 1. 检测当前TTY设备
    try:
        current_tty = os.ttyname(sys.stdin.fileno())
        print(f"当前TTY设备: {current_tty}")
    except Exception as e:
        print(f"无法检测当前TTY: {e}")
        current_tty = None
    
    # 2. 尝试常见的TTY设备
    tty_devices = ['/dev/tty1', '/dev/tty2', '/dev/tty3', '/dev/tty4', '/dev/tty5', '/dev/tty6']
    available_ttys = []
    
    for tty_dev in tty_devices:
        if os.path.exists(tty_dev):
            available_ttys.append(tty_dev)
            print(f"找到TTY设备: {tty_dev}")
    
    if not available_ttys:
        print("未找到可用的TTY设备")
        return False
    
    # 3. 测试写入TTY设备
    test_message = "TTY穿透测试消息"
    
    for tty_dev in available_ttys:
        try:
            print(f"\n测试写入 {tty_dev}...")
            
            # 尝试写入测试消息
            with open(tty_dev, 'w') as tty_file:
                # 移动到右下角
                tty_file.write("\033[24;70H")  # 假设24行70列
                tty_file.write(f"[TTY测试] {test_message}")
                tty_file.flush()
            
            print(f"成功写入 {tty_dev}")
            
            # 等待3秒让用户观察
            print("等待3秒，请观察是否在fbterm中看到测试消息...")
            time.sleep(3)
            
            # 清除测试消息
            with open(tty_dev, 'w') as tty_file:
                tty_file.write("\033[24;70H")
                tty_file.write(" " * 30)  # 清除消息
                tty_file.flush()
            
            print(f"已清除 {tty_dev} 的测试消息")
            
        except Exception as e:
            print(f"写入 {tty_dev} 失败: {e}")
    
    print("\n=== 测试完成 ===")
    print("如果看到了测试消息，说明TTY穿透机制可行")
    print("如果没有看到，可能需要其他方法")
    
    return True

if __name__ == "__main__":
    test_tty_penetration()
