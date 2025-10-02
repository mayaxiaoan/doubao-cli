#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTY1穿透测试脚本
自动在tty1各个位置显示测试信息
"""

import os
import sys
import time

def test_tty1_positions():
    """在tty1各个位置自动显示测试信息"""
    tty1_device = "/dev/tty1"
    
    if not os.path.exists(tty1_device):
        return False
    
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
            # 在tty1上写入测试消息
            with open(tty1_device, 'w') as tty_file:
                # 移动到指定位置
                tty_file.write(f"\033[{row};{col}H")
                tty_file.write(f"[{i+1}]TTY测试")
                tty_file.flush()
            
            # 等待2秒让用户观察
            time.sleep(2)
            
            # 清除测试消息
            with open(tty1_device, 'w') as tty_file:
                tty_file.write(f"\033[{row};{col}H")
                tty_file.write(" " * 15)  # 清除消息
                tty_file.flush()
            
        except Exception as e:
            pass
    
    return True

if __name__ == "__main__":
    test_tty1_positions()
