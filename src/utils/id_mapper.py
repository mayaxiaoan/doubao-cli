# -*- coding: utf-8 -*-
"""
ID映射模块

将长response_id映射为短id（约3位），便于用户使用和记忆。
支持持久化存储，程序重启后映射关系不丢失。
当达到上限时，自动循环使用旧的短id。
"""

import json
import os
from typing import Optional, Dict
from pathlib import Path


class IDMapper:
    """ID映射器
    
    功能：
    - 将长response_id转换为短id（3位十六进制字符）
    - 持久化保存映射关系
    - 支持双向查询（短id->长id, 长id->短id）
    - 达到上限后自动循环使用旧id
    - 使用混淆算法生成看似无规律的短id
    """
    
    MAX_IDS = 4096  # 最大短id数量（0x000 - 0xfff，16^3=4096）
    
    # 混淆密钥（用于XOR运算）
    XOR_KEY = 0xA5C
    
    # 字符替换表（打乱十六进制字符顺序，让短id更难看出规律）
    CHAR_MAP = str.maketrans('0123456789abcdef', '8d3a1fb95ce74062')
    
    def __init__(self, storage_file: str = "data/id_mapping.json"):
        """初始化ID映射器
        
        Args:
            storage_file: 映射数据存储文件路径
        """
        self.storage_file = storage_file
        self.short_to_long: Dict[str, str] = {}  # 短id -> 长id
        self.long_to_short: Dict[str, str] = {}  # 长id -> 短id
        self.counter: int = 0  # 当前计数器
        
        # 确保存储目录存在
        self._ensure_storage_dir()
        
        # 加载已有映射
        self._load_mappings()
    
    def _ensure_storage_dir(self) -> None:
        """确保存储目录存在"""
        storage_path = Path(self.storage_file)
        storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_mappings(self) -> None:
        """从文件加载映射关系"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.short_to_long = data.get('short_to_long', {})
                    self.long_to_short = data.get('long_to_short', {})
                    self.counter = data.get('counter', 0)
            except Exception as e:
                print(f"加载ID映射失败: {e}，将使用空映射")
                self.short_to_long = {}
                self.long_to_short = {}
                self.counter = 0
    
    def _save_mappings(self) -> None:
        """保存映射关系到文件"""
        try:
            data = {
                'short_to_long': self.short_to_long,
                'long_to_short': self.long_to_short,
                'counter': self.counter
            }
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存ID映射失败: {e}")
    
    def _number_to_short_id(self, num: int) -> str:
        """将数字转换为短id
        
        使用混淆算法生成看似无规律的3位十六进制短id：
        1. XOR运算混淆
        2. 位反转
        3. 字符替换
        4. 位置重排
        
        Args:
            num: 要转换的数字 (0-4095)
        
        Returns:
            3位十六进制短id字符串（如：4a7, e2f等）
        """
        # 步骤1: XOR混淆
        mixed = num ^ self.XOR_KEY
        
        # 步骤2: 位反转（反转12位二进制）
        reversed_bits = 0
        for i in range(12):
            if mixed & (1 << i):
                reversed_bits |= (1 << (11 - i))
        
        # 步骤3: 转为3位十六进制字符串
        hex_str = format(reversed_bits, '03x')
        
        # 步骤4: 字符替换（使用替换表）
        substituted = hex_str.translate(self.CHAR_MAP)
        
        # 步骤5: 位置重排 (abc -> cab)
        if len(substituted) == 3:
            reordered = substituted[2] + substituted[0] + substituted[1]
        else:
            reordered = substituted
        
        return reordered
    
    def get_or_create_short_id(self, long_id: str) -> str:
        """获取或创建短id
        
        如果长id已有对应的短id，直接返回；
        否则创建新的短id并保存映射关系。
        当达到上限时，循环使用旧的短id。
        
        Args:
            long_id: 长response_id
        
        Returns:
            对应的短id
        """
        # 检查是否已存在映射
        if long_id in self.long_to_short:
            return self.long_to_short[long_id]
        
        # 创建新的短id
        short_id = self._number_to_short_id(self.counter % self.MAX_IDS)
        
        # 如果短id已被占用（循环使用），需要清理旧映射
        if short_id in self.short_to_long:
            old_long_id = self.short_to_long[short_id]
            # 删除旧的反向映射
            if old_long_id in self.long_to_short:
                del self.long_to_short[old_long_id]
        
        # 保存新映射关系
        self.short_to_long[short_id] = long_id
        self.long_to_short[long_id] = short_id
        
        # 递增计数器
        self.counter += 1
        
        # 持久化保存
        self._save_mappings()
        
        return short_id
    
    def get_long_id(self, short_id: str) -> Optional[str]:
        """根据短id获取长id
        
        Args:
            short_id: 短id
        
        Returns:
            对应的长response_id，如果不存在返回None
        """
        return self.short_to_long.get(short_id)
    
    def get_short_id(self, long_id: str) -> Optional[str]:
        """根据长id获取短id（不创建新映射）
        
        Args:
            long_id: 长response_id
        
        Returns:
            对应的短id，如果不存在返回None
        """
        return self.long_to_short.get(long_id)
    
    def clear_all(self) -> None:
        """清空所有映射关系"""
        self.short_to_long.clear()
        self.long_to_short.clear()
        self.counter = 0
        self._save_mappings()
    
    def get_mapping_count(self) -> int:
        """获取当前映射数量"""
        return len(self.short_to_long)


# 全局ID映射器实例
_global_id_mapper: Optional[IDMapper] = None


def get_id_mapper() -> IDMapper:
    """获取全局ID映射器实例
    
    Returns:
        全局IDMapper实例
    """
    global _global_id_mapper
    if _global_id_mapper is None:
        _global_id_mapper = IDMapper()
    return _global_id_mapper

