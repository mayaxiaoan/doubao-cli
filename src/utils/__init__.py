# -*- coding: utf-8 -*-
"""
工具模块

提供输入处理、电池监控、编码处理、ID映射、历史记录等工具功能。
"""

from .input_handler import InputHandler
from .battery import BatteryMonitor, DummyBatteryMonitor, get_battery_monitor
from .encoding import setup_encoding
from .id_mapper import IDMapper, get_id_mapper
from .history import ChatHistory, get_chat_history

__all__ = [
    'InputHandler',
    'BatteryMonitor',
    'DummyBatteryMonitor',
    'get_battery_monitor',
    'setup_encoding',
    'IDMapper',
    'get_id_mapper',
    'ChatHistory',
    'get_chat_history'
]

