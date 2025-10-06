# -*- coding: utf-8 -*-
"""
聊天历史记录模块

使用 JSONL 格式保存聊天历史，提供：
- 增量写入和高效读取
- 自动维护最大记录数
- 历史查询和删除功能
- 短 ID 计数器恢复
"""

import json
import os
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ChatHistory:
    """聊天历史管理器
    
    功能：
    - 保存聊天对话记录（用户消息、AI 回复、短 ID、response_id）
    - 保存命令记录（#clear、#new 等）
    - 自动维护最大记录数（超出后删除旧记录）
    - 支持查询最近 N 轮对话
    - 从历史中恢复短 ID 计数器
    """
    
    def __init__(
        self,
        storage_file: str = "data/chat_history.jsonl",
        max_turns: int = 100
    ):
        """初始化历史管理器
        
        Args:
            storage_file: 历史记录文件路径（JSONL格式）
            max_turns: 最大保存轮次数
        """
        self.storage_file = storage_file
        self.max_turns = max_turns
        self.current_turn = 0  # 当前轮次编号
        
        # 确保存储目录存在
        self._ensure_storage_dir()
        
        # 初始化时读取当前轮次编号
        self._init_turn_number()
    
    def _ensure_storage_dir(self) -> None:
        """确保存储目录存在"""
        storage_path = Path(self.storage_file)
        storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _init_turn_number(self) -> None:
        """从历史记录中读取最后的轮次编号"""
        if not os.path.exists(self.storage_file):
            self.current_turn = 0
            return
        
        try:
            # 读取最后一行获取最大轮次编号
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                last_line = None
                for line in f:
                    if line.strip():
                        last_line = line
                
                if last_line:
                    record = json.loads(last_line)
                    self.current_turn = record.get('turn', 0)
        except Exception as e:
            print(f"读取历史轮次编号失败: {e}")
            self.current_turn = 0
    
    def save_chat_turn(
        self,
        short_id: str,
        response_id: str,
        user_message: str,
        bot_reply: str
    ) -> None:
        """保存一轮聊天记录
        
        Args:
            short_id: 短id
            response_id: 长response_id
            user_message: 用户消息
            bot_reply: AI回复（不含深度思考内容）
        """
        self.current_turn += 1
        
        record = {
            'turn': self.current_turn,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'chat',
            'short_id': short_id,
            'response_id': response_id,
            'user_message': user_message,
            'bot_reply': bot_reply
        }
        
        self._append_record(record)
        self._trim_history()
    
    def save_command(self, command: str, message: str) -> None:
        """保存命令记录（如#clear、#new等）
        
        Args:
            command: 命令名称
            message: 命令执行消息
        """
        self.current_turn += 1
        
        record = {
            'turn': self.current_turn,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'command',
            'command': command,
            'message': message
        }
        
        self._append_record(record)
        self._trim_history()
    
    def _append_record(self, record: Dict[str, Any]) -> None:
        """追加一条记录到文件
        
        Args:
            record: 记录字典
        """
        try:
            with open(self.storage_file, 'a', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False)
                f.write('\n')
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def _trim_history(self) -> None:
        """修剪历史记录，只保留最近max_turns条"""
        if not os.path.exists(self.storage_file):
            return
        
        try:
            # 读取所有记录
            records = []
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            
            # 如果超出限制，只保留最新的记录
            if len(records) > self.max_turns:
                records = records[-self.max_turns:]
                
                # 重写文件
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    for record in records:
                        json.dump(record, f, ensure_ascii=False)
                        f.write('\n')
        except Exception as e:
            print(f"修剪历史记录失败: {e}")
    
    def get_recent_history(self, n: int = 10) -> List[Dict[str, Any]]:
        """获取最近N轮对话记录
        
        Args:
            n: 要获取的轮次数
        
        Returns:
            历史记录列表（按时间正序）
        """
        if not os.path.exists(self.storage_file):
            return []
        
        try:
            # 使用deque读取最后N行
            records = deque(maxlen=n)
            
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            
            return list(records)
        except Exception as e:
            print(f"读取历史记录失败: {e}")
            return []
    
    def get_all_history(self) -> List[Dict[str, Any]]:
        """获取所有历史记录
        
        Returns:
            完整的历史记录列表（按时间正序）
        """
        if not os.path.exists(self.storage_file):
            return []
        
        try:
            records = []
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            
            return records
        except Exception as e:
            print(f"读取所有历史记录失败: {e}")
            return []
    
    def get_last_short_id_counter(self) -> int:
        """从历史记录中获取最后使用的短id计数器值
        
        Returns:
            最后的计数器值，如果没有记录则返回0
        """
        if not os.path.exists(self.storage_file):
            return 0
        
        try:
            # 从后向前读取，找到第一条chat类型的记录
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 倒序查找最后一条chat记录
            for line in reversed(lines):
                if line.strip():
                    try:
                        record = json.loads(line)
                        if record.get('type') == 'chat' and 'response_id' in record:
                            # 返回轮次编号作为计数器
                            # 因为每次chat都会生成一个新id，turn可以作为counter的参考
                            return record.get('turn', 0)
                    except json.JSONDecodeError:
                        continue
            
            return 0
        except Exception as e:
            print(f"读取短id计数器失败: {e}")
            return 0
    
    def get_total_turns(self) -> int:
        """获取总轮次数
        
        Returns:
            总轮次数
        """
        return self.current_turn
    
    def delete_recent_turns(self, n: int) -> int:
        """删除最近N轮历史记录
        
        Args:
            n: 要删除的轮次数
        
        Returns:
            实际删除的轮次数
        """
        if not os.path.exists(self.storage_file):
            return 0
        
        try:
            # 读取所有记录
            records = []
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            
            # 计算要删除的记录数
            total_records = len(records)
            if n <= 0:
                return 0
            
            # 如果要删除的数量大于等于总数，清空所有记录
            if n >= total_records:
                deleted_count = total_records
                os.remove(self.storage_file)
                self.current_turn = 0
                return deleted_count
            
            # 只保留前面的记录（删除最后n条）
            deleted_count = n
            remaining_records = records[:-n]
            
            # 更新当前轮次编号
            if remaining_records:
                self.current_turn = remaining_records[-1].get('turn', 0)
            else:
                self.current_turn = 0
            
            # 重写文件
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                for record in remaining_records:
                    json.dump(record, f, ensure_ascii=False)
                    f.write('\n')
            
            return deleted_count
        except Exception as e:
            print(f"删除历史记录失败: {e}")
            return 0
    
    def clear_all(self) -> None:
        """清空所有历史记录"""
        try:
            if os.path.exists(self.storage_file):
                os.remove(self.storage_file)
            self.current_turn = 0
        except Exception as e:
            print(f"清空历史记录失败: {e}")


# 全局历史管理器实例
_global_chat_history: Optional[ChatHistory] = None


def get_chat_history(max_turns: int = 100) -> ChatHistory:
    """获取全局历史管理器实例
    
    Args:
        max_turns: 最大保存轮次数
    
    Returns:
        全局ChatHistory实例
    """
    global _global_chat_history
    if _global_chat_history is None:
        _global_chat_history = ChatHistory(max_turns=max_turns)
    return _global_chat_history

