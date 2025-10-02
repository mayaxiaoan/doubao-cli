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
        self.is_charging = False
        self.stop_event = threading.Event()
        self.display_thread = None
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
        self.is_charging = False
    
    def _read_battery_info(self):
        """读取电池信息"""
        if self.is_desktop:
            return 100, False
        
        if not self.battery_path:
            return 100, False
        
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
                    return 100, False
            
            # 读取充电状态 - 针对MacBook优化
            is_charging = self._detect_charging_status()
            
            return level, is_charging
            
        except (IOError, ValueError, ZeroDivisionError):
            return 100, False
    
    def _detect_charging_status(self):
        """检测充电状态 - 针对MacBook Air 2010优化"""
        if not self.battery_path:
            return False
        
        # 方法1: 读取电池status文件
        status_file = os.path.join(self.battery_path, 'status')
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    status = f.read().strip().lower()
                    # MacBook的Full状态也应该显示为充电中
                    if status in ['charging', 'full']:
                        return True
            except:
                pass
        
        # 方法2: 检查AC适配器状态（MacBook Air 2010使用ADP1）
        ac_paths = [
            '/sys/class/power_supply/ADP1',  # MacBook常见路径
            '/sys/class/power_supply/AC',
            '/sys/class/power_supply/ac'
        ]
        
        for ac_path in ac_paths:
            if os.path.exists(ac_path):
                online_file = os.path.join(ac_path, 'online')
                if os.path.exists(online_file):
                    try:
                        with open(online_file, 'r') as f:
                            online = f.read().strip()
                            if online == '1':
                                return True
                    except:
                        pass
        
        # 方法3: 检查充电电流（备用方法）
        current_file = os.path.join(self.battery_path, 'current_now')
        if os.path.exists(current_file):
            try:
                with open(current_file, 'r') as f:
                    current = int(f.read().strip())
                    # 如果电流为正数，表示正在充电
                    if current > 0:
                        return True
            except:
                pass
        
        return False
    
    def get_battery_status(self):
        """获取电池状态信息"""
        level, charging = self._read_battery_info()
        self.current_level = level
        self.is_charging = charging
        return level, charging
    
    def _get_battery_icon(self, level, charging):
        """根据电量获取电池图标"""
        return "⚡"  # 统一使用闪电图标
    
    def _get_battery_color(self, level, charging):
        """根据电量获取颜色"""
        if charging:
            return COLORS.get('bright_green', '\033[92m')  # 充电中显示绿色
        elif level < 20:
            return COLORS.get('bright_red', '\033[91m')    # 低于20%显示红色
        else:
            return COLORS.get('bright_white', '\033[97m')  # 其他情况显示白色
    
    def _display_battery_info(self):
        """在右下角显示电池信息"""
        level, charging = self.get_battery_status()
        
        # 获取终端尺寸
        try:
            terminal_width, terminal_height = os.get_terminal_size().columns, os.get_terminal_size().lines
        except:
            terminal_width, terminal_height = 80, 24
        
        # 准备电池信息文本 - 使用新格式 ⚡[98%]
        if self.is_desktop:
            battery_text = "⚡[100%]"
            color = COLORS.get('bright_white', '\033[97m')
        else:
            battery_text = f"⚡[{level}%]"
            color = self._get_battery_color(level, charging)
        
        # 计算显示位置（右下角，始终靠右对齐）
        reset_color = COLORS.get('reset', '\033[0m')
        display_text = f"{color}{battery_text}{reset_color}"
        
        # 保存当前光标位置
        sys.stdout.write("\033[s")
        
        # 计算文本长度（考虑ANSI颜色代码不占用显示宽度）
        # 关键修复：确保文本不会超出终端边界
        text_length = len(battery_text)  # 只计算实际显示字符长度
        
        # 移动到右下角位置，确保不会换行
        # 使用更保守的方法：预留更多空间，确保不会换行
        max_text_length = 8  # 预留更多空间，避免边界问题
        # 关键修复：确保位置不会超出终端边界
        target_col = max(1, terminal_width - max_text_length)
        move_cursor = f"\033[{terminal_height};{target_col}H"
        
        # 先清除该位置的内容（用空格覆盖最大长度）
        sys.stdout.write(f"{move_cursor}{' ' * max_text_length}")
        
        # 再次移动到相同位置并显示电池信息
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
                time.sleep(10)  # 每10秒刷新一次
            except Exception:
                # 忽略显示错误，继续运行
                pass
    
    def clear_display(self):
        """清除电池显示"""
        try:
            terminal_width, terminal_height = os.get_terminal_size().columns, os.get_terminal_size().lines
            # 保存当前光标位置
            sys.stdout.write("\033[s")
            # 移动到右下角并清除（清除最大可能的文本长度）
            # 预留8个字符空间，避免边界问题
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
