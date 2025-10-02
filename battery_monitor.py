# -*- coding: utf-8 -*-
"""
电池电量监控模块
用于在Linux TTY模式下显示电池电量信息
"""

import os
import threading
import time
import sys
from config import COLORS, ENABLE_COLORS


class BatteryMonitor:
    """电池电量监控器"""
    
    def __init__(self):
        self.battery_path = None
        self.is_desktop = False
        self.current_level = 100
        self.stop_event = threading.Event()
        self.display_thread = None
        self.tty_device = "/dev/tty1"  # 固定使用tty1
        self._find_battery_path()
    
    def _find_battery_path(self):
        """查找电池信息文件路径"""
        # 常见的电池路径
        battery_paths = [
            '/sys/class/power_supply/BAT0',
            '/sys/class/power_supply/BAT1',
            '/sys/class/power_supply/Battery',
            '/proc/acpi/battery/BAT0',
            '/proc/acpi/battery/BAT1'
        ]
        
        for path in battery_paths:
            if os.path.exists(path):
                # 检查是否有capacity文件
                capacity_files = ['capacity', 'energy_now', 'charge_now']
                for cap_file in capacity_files:
                    if os.path.exists(os.path.join(path, cap_file)):
                        self.battery_path = path
                        return
        
        # 如果没有找到电池，判断为台式机
        self.is_desktop = True
        self.current_level = 100
    
    def _read_battery_info(self):
        """读取电池信息"""
        if self.is_desktop:
            return 100
        
        if not self.battery_path:
            return 100
        
        try:
            # 读取电量百分比
            capacity_file = os.path.join(self.battery_path, 'capacity')
            if os.path.exists(capacity_file):
                with open(capacity_file, 'r') as f:
                    level = int(f.read().strip())
            else:
                # 尝试从energy_now和energy_full计算
                energy_now_file = os.path.join(self.battery_path, 'energy_now')
                energy_full_file = os.path.join(self.battery_path, 'energy_full')
                if os.path.exists(energy_now_file) and os.path.exists(energy_full_file):
                    with open(energy_now_file, 'r') as f:
                        energy_now = int(f.read().strip())
                    with open(energy_full_file, 'r') as f:
                        energy_full = int(f.read().strip())
                    level = int((energy_now / energy_full) * 100)
                else:
                    return 100
            
            return level
            
        except (IOError, ValueError, ZeroDivisionError):
            return 100
    
    def get_battery_status(self):
        """获取电池状态信息"""
        level = self._read_battery_info()
        self.current_level = level
        return level
    
    
    def _get_battery_color(self, level):
        """根据电量获取TTY颜色"""
        if level < 20:
            return '\033[31m'  # 红色
        elif level < 50:
            return '\033[33m'  # 黄色
        else:
            return '\033[32m'  # 绿色
    
    def _display_battery_info(self):
        """在TTY上显示电池信息"""
        level = self.get_battery_status()
        
        # 准备电池信息文本 - 使用新格式 pow[98%]
        if self.is_desktop:
            battery_text = "pow[100%]"
            color = '\033[33m'  # 默认黄色
        else:
            battery_text = f"pow[{level}%]"
            color = self._get_battery_color(level)
        
        # TTY颜色重置
        reset_color = '\033[0m'
        display_text = f"{color}{battery_text}{reset_color}"
        
        try:
            # 直接写入TTY设备
            with open(self.tty_device, 'w') as tty_file:
                # 移动到指定位置 (1, 116) - 向左偏移4个字符
                tty_file.write("\033[1;116H")
                
                # 先清除该位置的内容
                tty_file.write(" " * 12)  # 增加清除长度，因为pow[100%]比⚡[100%]长
                
                # 再次移动到相同位置并显示电池信息
                tty_file.write("\033[1;116H")
                tty_file.write(display_text)
                tty_file.flush()
                
        except Exception:
            # 如果TTY写入失败，静默忽略
            pass
    
    def start_display(self):
        """开始显示电池信息"""
        if self.display_thread and self.display_thread.is_alive():
            return
        
        self.stop_event.clear()
        self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self.display_thread.start()
    
    def refresh_now(self):
        """立即刷新电池显示位置"""
        try:
            self._display_battery_info()
        except Exception:
            # 忽略刷新错误
            pass
    
    def hide_display(self):
        """隐藏电池显示"""
        try:
            self.clear_display()
        except Exception:
            # 忽略清除错误
            pass
    
    def stop_display(self):
        """停止显示电池信息"""
        self.stop_event.set()
        if self.display_thread:
            self.display_thread.join(timeout=1)
    
    def _display_loop(self):
        """显示循环"""
        while not self.stop_event.is_set():
            try:
                self._display_battery_info()
                time.sleep(5)  # 每5秒刷新一次
            except Exception:
                # 忽略显示错误，继续运行
                pass
    
    def clear_display(self):
        """清除TTY电池显示"""
        try:
            # 直接写入TTY设备清除
            with open(self.tty_device, 'w') as tty_file:
                tty_file.write("\033[1;116H")
                tty_file.write(" " * 12)  # 清除电池信息
                tty_file.flush()
        except Exception:
            # 如果TTY清除失败，静默忽略
            pass


# 全局电池监控器实例
battery_monitor = BatteryMonitor()
