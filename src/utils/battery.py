# -*- coding: utf-8 -*-
"""
电池监控模块

用于在 Linux TTY 模式下显示电池电量信息，提供：
- 实时电量监控
- 自适应刷新间隔（根据电量和用户活动状态调整）
- TTY 终端显示
"""

import os
import platform
import threading
import time
from typing import Optional

from ..config import (
    BATTERY_DISPLAY_ENABLED,
    BATTERY_HIGH_LEVEL_THRESHOLD,
    BATTERY_REFRESH_INTERVAL,
    BATTERY_USER_IDLE_THRESHOLD,
)


class BatteryMonitor:
    """电池电量监控器
    
    在 Linux 系统的 TTY 终端上显示电池电量信息。
    支持自适应刷新间隔以节省能耗。
    """
    
    def __init__(self):
        self.battery_path: Optional[str] = None
        self.is_desktop: bool = False
        self.current_level: int = 100
        self.stop_event = threading.Event()
        self.display_thread: Optional[threading.Thread] = None
        self.tty_device: str = "/dev/tty1"
        
        # 自适应刷新相关
        self.last_user_activity_time: float = time.time()
        self.activity_lock = threading.Lock()
        
        self._find_battery_path()
    
    def _find_battery_path(self) -> None:
        """查找电池信息文件路径"""
        battery_paths = [
            '/sys/class/power_supply/BAT0',
            '/sys/class/power_supply/BAT1',
            '/sys/class/power_supply/Battery',
            '/proc/acpi/battery/BAT0',
            '/proc/acpi/battery/BAT1'
        ]
        
        for path in battery_paths:
            if os.path.exists(path):
                capacity_files = ['capacity', 'energy_now', 'charge_now']
                for cap_file in capacity_files:
                    if os.path.exists(os.path.join(path, cap_file)):
                        self.battery_path = path
                        return
        
        # 如果没有找到电池，判断为台式机
        self.is_desktop = True
        self.current_level = 100
    
    def _read_battery_info(self) -> int:
        """读取电池信息"""
        if self.is_desktop or not self.battery_path:
            return 100
        
        try:
            capacity_file = os.path.join(self.battery_path, 'capacity')
            if os.path.exists(capacity_file):
                with open(capacity_file, 'r') as f:
                    return int(f.read().strip())
            else:
                # 尝试从energy_now和energy_full计算
                energy_now_file = os.path.join(self.battery_path, 'energy_now')
                energy_full_file = os.path.join(self.battery_path, 'energy_full')
                if os.path.exists(energy_now_file) and os.path.exists(energy_full_file):
                    with open(energy_now_file, 'r') as f:
                        energy_now = int(f.read().strip())
                    with open(energy_full_file, 'r') as f:
                        energy_full = int(f.read().strip())
                    return int((energy_now / energy_full) * 100)
                else:
                    return 100
        except (IOError, ValueError, ZeroDivisionError):
            return 100
    
    def get_battery_status(self) -> int:
        """获取电池状态信息"""
        level = self._read_battery_info()
        self.current_level = level
        return level
    
    def update_user_activity(self) -> None:
        """更新用户活动时间戳
        
        在用户有交互操作时调用此方法，用于自适应刷新间隔计算。
        """
        with self.activity_lock:
            self.last_user_activity_time = time.time()
    
    def _calculate_refresh_interval(self) -> float:
        """计算当前应使用的刷新间隔
        
        根据电池电量和用户活动状态动态计算刷新间隔。
        
        规则1：电量充足（40%以上）时倍率为3，否则为1
        规则2：用户1分钟以上无活动时倍率为2，否则为1
        最终间隔 = 基础间隔 * (规则1倍率 + 规则2倍率)
        
        Returns:
            计算后的刷新间隔（秒）
        """
        # 规则1：根据电量计算倍率
        battery_multiplier = 3 if self.current_level >= BATTERY_HIGH_LEVEL_THRESHOLD else 1
        
        # 规则2：根据用户活动计算倍率
        with self.activity_lock:
            time_since_activity = time.time() - self.last_user_activity_time
        
        idle_multiplier = 2 if time_since_activity >= BATTERY_USER_IDLE_THRESHOLD else 1
        
        # 计算最终刷新间隔
        total_multiplier = battery_multiplier + idle_multiplier
        refresh_interval = BATTERY_REFRESH_INTERVAL * total_multiplier
        
        return refresh_interval
    
    def _get_battery_color(self, level: int) -> str:
        """根据电量获取TTY颜色"""
        if level < 20:
            return '\033[31m'  # 红色
        elif level < 40:
            return '\033[33m'  # 黄色
        else:
            return '\033[32m'  # 绿色
    
    def _display_battery_info(self) -> None:
        """在TTY上显示电池信息"""
        level = self.get_battery_status()
        
        # 准备电池信息文本
        if self.is_desktop:
            battery_text = "Pow[100%]"
            color = '\033[33m'
        else:
            battery_text = f"Pow[{level}%]"
            color = self._get_battery_color(level)
        
        reset_color = '\033[0m'
        
        try:
            with open(self.tty_device, 'w') as tty_file:
                max_length = 9  # Pow[100%]的最大长度
                padding_spaces = max_length - len(battery_text)
                padded_text = " " * padding_spaces + battery_text
                
                # 逐字显示电池信息，实现淡入效果
                for i in range(len(padded_text) + 1):
                    tty_file.write("\033[1;116H")
                    current_text = padded_text[:i]
                    current_display = f"{color}{current_text}{reset_color}"
                    tty_file.write(current_display)
                    tty_file.flush()
                    
                    if i < len(padded_text):
                        time.sleep(0.1)
        except Exception:
            pass
    
    def start_display(self) -> None:
        """开始显示电池信息"""
        if not BATTERY_DISPLAY_ENABLED:
            return
        
        if self.display_thread and self.display_thread.is_alive():
            return
        
        self.stop_event.clear()
        self.display_thread = threading.Thread(
            target=self._display_loop,
            daemon=True
        )
        self.display_thread.start()
    
    def stop_display(self) -> None:
        """停止显示电池信息"""
        self.stop_event.set()
        if self.display_thread:
            self.display_thread.join(timeout=1)
        self.clear_display()
    
    def _display_loop(self) -> None:
        """显示循环（支持自适应刷新间隔）"""
        while not self.stop_event.is_set():
            try:
                # 显示电池信息
                self._display_battery_info()
                
                # 动态计算下次刷新间隔
                refresh_interval = self._calculate_refresh_interval()
                
                # 使用 wait() 而不是 sleep()，这样可以响应 stop_event
                # 同时避免因刷新间隔变化导致永远到不了下个刷新时间点
                self.stop_event.wait(timeout=refresh_interval)
                
            except Exception:
                pass
    
    def clear_display(self) -> None:
        """清除TTY电池显示"""
        try:
            with open(self.tty_device, 'w') as tty_file:
                tty_file.write("\033[1;116H")
                tty_file.write(" " * 9)
                tty_file.flush()
        except Exception:
            pass
    
    def refresh_now(self) -> None:
        """立即刷新电池显示"""
        if BATTERY_DISPLAY_ENABLED:
            try:
                self._display_battery_info()
            except Exception:
                pass
    
    def hide_display(self) -> None:
        """隐藏电池显示"""
        if BATTERY_DISPLAY_ENABLED:
            try:
                self.clear_display()
            except Exception:
                pass


class DummyBatteryMonitor:
    """Windows 下的空操作电池监控器"""
    
    def start_display(self) -> None:
        pass
    
    def stop_display(self) -> None:
        pass
    
    def refresh_now(self) -> None:
        pass
    
    def hide_display(self) -> None:
        pass
    
    def clear_display(self) -> None:
        pass
    
    def update_user_activity(self) -> None:
        """空实现，保持接口一致"""
        pass
    
    @staticmethod
    def get_battery_status() -> int:
        return 100


def get_battery_monitor():
    """获取适合当前系统的电池监控器实例"""
    if platform.system() == 'Windows':
        return DummyBatteryMonitor()
    else:
        return BatteryMonitor()

