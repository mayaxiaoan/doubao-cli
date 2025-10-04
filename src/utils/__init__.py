# -*- coding: utf-8 -*-
"""
工具模块

提供输入处理、电池监控、编码处理等工具功能。
"""

from .input_handler import InputHandler
from .battery import BatteryMonitor, DummyBatteryMonitor, get_battery_monitor
from .encoding import setup_encoding

__all__ = [
    'InputHandler',
    'BatteryMonitor',
    'DummyBatteryMonitor',
    'get_battery_monitor',
    'setup_encoding'
]

