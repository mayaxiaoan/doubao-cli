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
        self.tty_device = None  # TTY设备路径
        self._find_battery_path()
        self._find_tty_device()
    
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
    
    def _find_tty_device(self):
        """查找TTY设备路径"""
        try:
            # 获取当前进程的TTY设备
            tty_name = os.ttyname(sys.stdin.fileno())
            if tty_name:
                self.tty_device = tty_name
            else:
                # 备用方法：尝试常见的TTY设备
                tty_devices = ['/dev/tty1', '/dev/tty2', '/dev/tty3', '/dev/tty4', '/dev/tty5', '/dev/tty6']
                for tty_dev in tty_devices:
                    if os.path.exists(tty_dev):
                        self.tty_device = tty_dev
                        break
        except Exception:
            # 如果无法找到TTY设备，使用None
            self.tty_device = None
    
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
        """根据电量获取颜色"""
        if level < 20:
            return COLORS.get('bright_red', '\033[91m')    # 低于20%显示红色
        else:
            return COLORS.get('bright_white', '\033[97m')  # 其他情况显示白色
    
    def _display_battery_info(self):
        """在TTY设备上显示电池信息（穿透fbterm）"""
        if not self.tty_device:
            # 如果没有TTY设备，回退到普通显示
            self._display_battery_info_fallback()
            return
        
        level = self.get_battery_status()
        
        # 准备电池信息文本 - 使用新格式 ⚡[98%]
        if self.is_desktop:
            battery_text = "⚡[100%]"
            color = COLORS.get('bright_white', '\033[97m')
        else:
            battery_text = f"⚡[{level}%]"
            color = self._get_battery_color(level)
        
        # 计算显示位置（右下角）
        reset_color = COLORS.get('reset', '\033[0m')
        display_text = f"{color}{battery_text}{reset_color}"
        
        try:
            # 直接写入TTY设备
            with open(self.tty_device, 'w') as tty_file:
                # 获取终端尺寸
                try:
                    terminal_width, terminal_height = os.get_terminal_size().columns, os.get_terminal_size().lines
                except:
                    terminal_width, terminal_height = 80, 24
                
                # 移动到右下角位置
                max_text_length = 8
                target_col = max(1, terminal_width - max_text_length)
                move_cursor = f"\033[{terminal_height};{target_col}H"
                
                # 先清除该位置的内容
                tty_file.write(f"{move_cursor}{' ' * max_text_length}")
                
                # 显示电池信息
                tty_file.write(f"{move_cursor}{display_text}")
                tty_file.flush()
                
        except Exception:
            # 如果TTY写入失败，回退到普通显示
            self._display_battery_info_fallback()
    
    def _display_battery_info_fallback(self):
        """回退显示方法（在fbterm内显示）"""
        level = self.get_battery_status()
        
        # 获取终端尺寸
        try:
            terminal_width, terminal_height = os.get_terminal_size().columns, os.get_terminal_size().lines
        except:
            terminal_width, terminal_height = 80, 24
        
        # 准备电池信息文本
        if self.is_desktop:
            battery_text = "⚡[100%]"
            color = COLORS.get('bright_white', '\033[97m')
        else:
            battery_text = f"⚡[{level}%]"
            color = self._get_battery_color(level)
        
        # 计算显示位置（右下角）
        reset_color = COLORS.get('reset', '\033[0m')
        display_text = f"{color}{battery_text}{reset_color}"
        
        # 保存当前光标位置
        sys.stdout.write("\033[s")
        
        # 移动到右下角位置
        max_text_length = 8
        target_col = max(1, terminal_width - max_text_length)
        move_cursor = f"\033[{terminal_height};{target_col}H"
        
        # 先清除该位置的内容
        sys.stdout.write(f"{move_cursor}{' ' * max_text_length}")
        
        # 显示电池信息
        sys.stdout.write(f"{move_cursor}{display_text}")
        
        # 恢复光标位置
        sys.stdout.write("\033[u")
        sys.stdout.flush()
    
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
        """清除电池显示"""
        if not self.tty_device:
            # 如果没有TTY设备，使用普通清除方法
            self._clear_display_fallback()
            return
        
        try:
            # 直接写入TTY设备清除
            with open(self.tty_device, 'w') as tty_file:
                terminal_width, terminal_height = os.get_terminal_size().columns, os.get_terminal_size().lines
                target_col = max(1, terminal_width - 8)
                move_cursor = f"\033[{terminal_height};{target_col}H"
                tty_file.write(f"{move_cursor}{' ' * 8}")
                tty_file.flush()
        except Exception:
            # 如果TTY清除失败，使用回退方法
            self._clear_display_fallback()
    
    def _clear_display_fallback(self):
        """回退清除方法"""
        try:
            terminal_width, terminal_height = os.get_terminal_size().columns, os.get_terminal_size().lines
            # 保存当前光标位置
            sys.stdout.write("\033[s")
            # 移动到右下角并清除
            target_col = max(1, terminal_width - 8)
            move_cursor = f"\033[{terminal_height};{target_col}H"
            sys.stdout.write(f"{move_cursor}{' ' * 8}")
            # 恢复光标位置
            sys.stdout.write("\033[u")
            sys.stdout.flush()
        except:
            pass


# 全局电池监控器实例
battery_monitor = BatteryMonitor()
