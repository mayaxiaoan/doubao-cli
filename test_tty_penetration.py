#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTY1穿透测试脚本
专门测试tty1终端的穿透显示功能
"""

import os
import sys
import time

def test_tty1_positions():
    """测试tty1不同位置的穿透显示"""
    print("=== TTY1穿透位置测试 ===")
    
    tty1_device = "/dev/tty1"
    
    if not os.path.exists(tty1_device):
        print(f"错误: {tty1_device} 不存在")
        return False
    
    print(f"测试设备: {tty1_device}")
    
    # 定义不同的测试位置
    test_positions = [
        # (行, 列, 描述)
        (1, 70, "右上角"),
        (1, 1, "左上角"),
        (24, 70, "右下角"),
        (24, 1, "左下角"),
        (12, 70, "右中"),
        (12, 1, "左中"),
        (6, 70, "右上偏中"),
        (18, 70, "右下偏中"),
        (1, 50, "右上偏左"),
        (24, 50, "右下偏左"),
    ]
    
    for i, (row, col, description) in enumerate(test_positions):
        try:
            print(f"\n=== 准备测试位置 {i+1}: {description} (行{row}, 列{col}) ===")
            print("fbterm提示：即将在tty1上显示测试信息...")
            print("请观察屏幕，1秒后将在tty1上显示测试消息")
            
            # 延迟1秒，让fbterm的提示信息先显示
            time.sleep(1)
            
            # 现在在tty1上写入测试消息
            with open(tty1_device, 'w') as tty_file:
                # 移动到指定位置
                tty_file.write(f"\033[{row};{col}H")
                tty_file.write(f"[{i+1}]TTY测试")
                tty_file.flush()
            
            print(f"✓ 已在tty1位置 {i+1} 显示测试消息")
            print("请观察是否能看到测试消息...")
            print("按回车继续下一个测试...")
            
            # 等待用户确认
            input()
            
            # 清除测试消息
            print("正在清除tty1上的测试消息...")
            with open(tty1_device, 'w') as tty_file:
                tty_file.write(f"\033[{row};{col}H")
                tty_file.write(" " * 15)  # 清除消息
                tty_file.flush()
            
            print(f"✓ 已清除位置 {i+1}")
            
        except Exception as e:
            print(f"测试位置 {i+1} 失败: {e}")
    
    print("\n=== 测试完成 ===")
    print("请告诉我哪个位置能够成功穿透显示")
    
    return True

def test_tty1_timing():
    """测试tty1的时序穿透"""
    print("\n=== TTY1时序测试 ===")
    
    tty1_device = "/dev/tty1"
    
    print("将在不同时间间隔测试穿透显示...")
    
    # 测试不同的时间间隔
    intervals = [1, 2, 3, 5, 10]  # 秒
    
    for interval in intervals:
        try:
            print(f"\n=== 准备测试间隔: {interval}秒 ===")
            print("fbterm提示：即将在tty1上显示时序测试信息...")
            print(f"请观察屏幕，1秒后将在tty1上显示 {interval}秒间隔测试")
            
            # 延迟1秒，让fbterm的提示信息先显示
            time.sleep(1)
            
            # 现在在tty1上写入测试消息
            with open(tty1_device, 'w') as tty_file:
                tty_file.write("\033[24;60H")  # 右下角偏左
                tty_file.write(f"[{interval}s]时序测试")
                tty_file.flush()
            
            print(f"✓ 已在tty1上显示 {interval}秒间隔测试")
            print("请观察是否能看到测试消息...")
            
            # 等待指定时间
            print(f"等待 {interval} 秒...")
            time.sleep(interval)
            
            # 清除测试消息
            print("正在清除tty1上的测试消息...")
            with open(tty1_device, 'w') as tty_file:
                tty_file.write("\033[24;60H")
                tty_file.write(" " * 15)
                tty_file.flush()
            
            print(f"✓ 已清除 {interval}秒间隔测试")
            
        except Exception as e:
            print(f"时序测试 {interval}秒 失败: {e}")
    
    print("\n=== 时序测试完成 ===")

if __name__ == "__main__":
    print("TTY1穿透测试脚本")
    print("请确保在fbterm中运行此脚本")
    print()
    
    choice = input("选择测试类型:\n1. 位置测试\n2. 时序测试\n3. 全部测试\n请输入选择 (1/2/3): ")
    
    if choice == "1":
        test_tty1_positions()
    elif choice == "2":
        test_tty1_timing()
    elif choice == "3":
        test_tty1_positions()
        test_tty1_timing()
    else:
        print("无效选择，运行位置测试...")
        test_tty1_positions()
