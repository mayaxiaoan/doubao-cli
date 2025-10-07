# -*- coding: utf-8 -*-
"""
ID 映射模块

将长 response_id 映射为短 ID（3 位），提供：
- 短 ID 生成（基于混淆算法）
- ID 映射管理（懒加载模式，按需从历史查询）
- 循环复用机制（达到上限后自动循环）
- 基于 API_KEY 的个性化短 ID 规则
- LRU 缓存优化查询性能
"""

from typing import Dict, Optional
from collections import OrderedDict


class IDMapper:
    """ID 映射器（懒加载版本）
    
    功能：
    - 将长 response_id 转换为短 ID（3 位十六进制字符）
    - 懒加载模式：按需从历史文件查询，不预加载所有映射
    - LRU 缓存：保留最近使用的映射，提升常用 ID 查询速度
    - 支持短 ID 查询长 ID（用于用户继续指定对话）
    - 达到上限后自动循环使用旧 ID
    - 使用混淆算法生成看似无规律的短 ID
    - 基于 API_KEY 生成独特的混淆参数，不同用户的短 ID 规则不同
    
    设计理念（低内存优化版本）：
    - 启动时只恢复 counter，不加载所有映射关系
    - 使用懒加载：当用户使用短 ID 时，才从历史文件中查找
    - LRU 缓存：只保留最近使用的 100 个映射在内存中
    - 单一数据源：所有映射关系由 chat_history.jsonl 管理
    - 适合长期运行和轻量级平台
    """
    
    MAX_IDS = 4096  # 最大短 ID 数量（0x000 - 0xfff，16^3=4096）
    CACHE_SIZE = 100  # LRU 缓存大小（只保留最近 100 个映射）
    
    def __init__(self):
        """初始化 ID 映射器（懒加载模式）
        
        从 config 中读取 API_KEY，生成唯一的混淆参数。
        只恢复 counter，不预加载映射关系。
        """
        # 使用 OrderedDict 实现 LRU 缓存
        self.short_to_long: OrderedDict[str, str] = OrderedDict()
        self.counter: int = 0  # 当前计数器
        
        # 基于 API_KEY 生成混淆参数
        self._init_obfuscation_params()
        
        # 从历史记录恢复计数器（不加载映射）
        self._restore_counter_from_history()
    
    def _init_obfuscation_params(self) -> None:
        """基于API_KEY初始化混淆参数
        
        使用API_KEY的一部分直接生成：
        1. XOR_KEY: 用于XOR运算的12位混淆密钥
        2. CHAR_MAP: 字符替换表
        
        这样不同的API_KEY会产生不同的短id规则，提高安全性。
        """
        from ..config import ARK_API_KEY
        
        # 从API_KEY中提取字符，计算XOR_KEY (12位，范围0-4095)
        # 取前3个字符的ASCII值相加，模4096
        key_part = ARK_API_KEY[:3] if len(ARK_API_KEY) >= 3 else ARK_API_KEY
        self.XOR_KEY = sum(ord(c) for c in key_part) % 4096
        
        # 生成CHAR_MAP：基于API_KEY的字符ASCII值来确定性地排列
        # 取API_KEY的第4-19个字符(共16个)，用它们的ASCII值作为映射
        hex_original = '0123456789abcdef'
        
        # 如果API_KEY足够长，用它来构造新的字符映射
        if len(ARK_API_KEY) >= 19:
            # 取第4-19个字符的ASCII值，对16取模，得到16个索引
            indices = [ord(ARK_API_KEY[i]) % 16 for i in range(3, 19)]
            # 根据索引重排hex字符
            hex_shuffled = ''.join(hex_original[idx] for idx in indices)
        else:
            # API_KEY较短时，通过简单的位移重排
            shift = sum(ord(c) for c in ARK_API_KEY) % 16
            hex_shuffled = hex_original[shift:] + hex_original[:shift]
        
        self.CHAR_MAP = str.maketrans(hex_original, hex_shuffled)
    
    def _restore_counter_from_history(self) -> None:
        """从聊天历史恢复计数器（不加载映射关系）
        
        只读取最后一条记录获取 counter，大幅减少启动内存占用。
        """
        try:
            # 延迟导入避免循环依赖
            from .history import get_chat_history
            
            history = get_chat_history()
            
            # 只获取最近1条记录来恢复counter
            recent_records = history.get_recent_history(n=1)
            
            if not recent_records:
                self.counter = 0
                return
            
            # 从最后一条记录获取轮次作为counter
            last_record = recent_records[-1]
            if last_record.get('type') == 'chat':
                self.counter = last_record.get('turn', 0)
            else:
                self.counter = 0
        
        except Exception as e:
            # 静默失败，从0开始
            print(f"从历史恢复counter失败: {e}，将从0开始")
            self.counter = 0
    
    def _lookup_from_history(self, short_id: str) -> Optional[str]:
        """从历史文件中查找短 ID 对应的长 ID（懒加载）
        
        当缓存中没有时，从历史文件中查找。
        这个操作可能较慢，但内存占用极低。
        
        Args:
            short_id: 短 ID
        
        Returns:
            对应的长 response_id，如果不存在返回 None
        """
        try:
            # 延迟导入避免循环依赖
            from .history import get_chat_history
            
            history = get_chat_history()
            
            # 遍历所有历史记录查找匹配的短ID
            # 注意：这个操作相对较慢，但用户不要求速度
            records = history.get_all_history()
            
            for record in records:
                if record.get('type') == 'chat':
                    if record.get('short_id') == short_id:
                        long_id = record.get('response_id')
                        if long_id:
                            # 找到后加入缓存
                            self._add_to_cache(short_id, long_id)
                            return long_id
            
            return None
        
        except Exception as e:
            print(f"从历史查找ID失败: {e}")
            return None
    
    def _add_to_cache(self, short_id: str, long_id: str) -> None:
        """添加映射到 LRU 缓存
        
        Args:
            short_id: 短 ID
            long_id: 长 response_id
        """
        # 如果已存在，先删除（保证重新插入到末尾）
        if short_id in self.short_to_long:
            del self.short_to_long[short_id]
        
        # 添加到末尾
        self.short_to_long[short_id] = long_id
        
        # 如果超过缓存大小，删除最早的
        if len(self.short_to_long) > self.CACHE_SIZE:
            self.short_to_long.popitem(last=False)  # 删除最早的项
    
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
        """创建短 ID
        
        为新的 response_id 创建对应的短 ID。
        当达到上限时，循环使用旧的短 ID（会覆盖缓存中的旧映射）。
        
        Args:
            long_id: 长 response_id
        
        Returns:
            对应的短 ID
        """
        # 创建新的短 ID
        short_id = self._number_to_short_id(self.counter % self.MAX_IDS)
        
        # 添加到 LRU 缓存（自动管理缓存大小）
        self._add_to_cache(short_id, long_id)
        
        # 递增计数器
        self.counter += 1
        
        # 注意：映射关系由 chat_history.jsonl 持久化管理
        
        return short_id
    
    def get_long_id(self, short_id: str) -> Optional[str]:
        """根据短 ID 获取长 ID（懒加载模式）
        
        先从缓存查找，如果没有则从历史文件中查找。
        
        Args:
            short_id: 短 ID
        
        Returns:
            对应的长 response_id，如果不存在返回 None
        """
        # 先从缓存查找
        long_id = self.short_to_long.get(short_id)
        
        if long_id:
            # 缓存命中，移到末尾（LRU更新）
            self.short_to_long.move_to_end(short_id)
            return long_id
        
        # 缓存未命中，从历史文件中查找
        return self._lookup_from_history(short_id)
    
    def clear_all(self) -> None:
        """清空所有映射关系（清空缓存）"""
        self.short_to_long.clear()
        self.counter = 0
    
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

