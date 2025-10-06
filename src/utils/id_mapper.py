# -*- coding: utf-8 -*-
"""
ID映射模块

将长response_id映射为短id（约3位），便于用户使用和记忆。
映射关系从聊天历史中恢复，不单独存储。
当达到上限时，自动循环使用旧的短id。
"""

from typing import Optional, Dict


class IDMapper:
    """ID映射器
    
    功能：
    - 将长response_id转换为短id（3位十六进制字符）
    - 从聊天历史恢复映射关系（内存存储）
    - 支持短id查询长id（用于用户继续指定对话）
    - 达到上限后自动循环使用旧id
    - 使用混淆算法生成看似无规律的短id
    - 基于API_KEY生成独特的混淆参数，不同用户的短id规则不同
    
    设计理念：
    - 映射关系不单独持久化，启动时从chat_history.jsonl重建
    - 只有历史中存在的对话才能继续，这是合理的限制
    - 单一数据源，避免数据不一致
    - 使用API_KEY作为种子，让每个用户的短id生成规则唯一
    """
    
    MAX_IDS = 4096  # 最大短id数量（0x000 - 0xfff，16^3=4096）
    
    def __init__(self):
        """初始化ID映射器
        
        从config中读取API_KEY，生成唯一的混淆参数
        """
        self.short_to_long: Dict[str, str] = {}  # 短id -> 长id
        self.counter: int = 0  # 当前计数器
        
        # 基于API_KEY生成混淆参数
        self._init_obfuscation_params()
        
        # 从历史记录恢复映射和计数器
        self._restore_from_history()
    
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
    
    def _restore_from_history(self) -> None:
        """从聊天历史恢复映射关系和计数器
        
        从chat_history.jsonl读取所有记录，重建内存映射
        """
        try:
            # 延迟导入避免循环依赖
            from .history import get_chat_history
            
            history = get_chat_history()
            
            # 获取所有历史记录（不限制数量，读取全部）
            records = history.get_all_history()
            
            if not records:
                self.counter = 0
                return
            
            # 从历史记录重建映射
            max_turn = 0
            for record in records:
                if record.get('type') == 'chat':
                    short_id = record.get('short_id')
                    response_id = record.get('response_id')
                    turn = record.get('turn', 0)
                    
                    if short_id and response_id:
                        self.short_to_long[short_id] = response_id
                    
                    # 跟踪最大轮次
                    if turn > max_turn:
                        max_turn = turn
            
            # 设置计数器为最大轮次（下一个id将从max_turn开始生成）
            self.counter = max_turn
        
        except Exception as e:
            # 静默失败，使用空映射
            print(f"从历史恢复映射失败: {e}，将从0开始")
            self.short_to_long = {}
            self.counter = 0
    
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
        """创建短id
        
        为新的response_id创建对应的短id。
        当达到上限时，循环使用旧的短id（会覆盖旧映射）。
        
        Args:
            long_id: 长response_id
        
        Returns:
            对应的短id
        """
        # 创建新的短id
        short_id = self._number_to_short_id(self.counter % self.MAX_IDS)
        
        # 保存映射关系（如果循环使用，会自动覆盖旧映射）
        self.short_to_long[short_id] = long_id
        
        # 递增计数器
        self.counter += 1
        
        # 注意：不再持久化保存，映射关系由chat_history.jsonl管理
        
        return short_id
    
    def get_long_id(self, short_id: str) -> Optional[str]:
        """根据短id获取长id
        
        Args:
            short_id: 短id
        
        Returns:
            对应的长response_id，如果不存在返回None
        """
        return self.short_to_long.get(short_id)
    
    def clear_all(self) -> None:
        """清空所有映射关系（仅清空内存）"""
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

