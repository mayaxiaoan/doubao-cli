# -*- coding: utf-8 -*-
"""
UI模块

提供终端界面显示相关功能。
"""

import threading
import time
from typing import Callable

from .config import SYMBOLS, COLORS, ENABLE_COLORS


def colored_print(
    text: str,
    color_key: str = 'reset',
    end: str = '\n',
    flush: bool = False
) -> None:
    """带颜色的安全打印函数
    
    Args:
        text: 要打印的文本
        color_key: 颜色键名
        end: 行尾字符
        flush: 是否立即刷新输出
    """
    if ENABLE_COLORS and color_key in COLORS:
        colored_text = f"{COLORS[color_key]}{text}{COLORS['reset']}"
    else:
        colored_text = text
    
    try:
        print(colored_text, end=end, flush=flush)
    except UnicodeEncodeError:
        try:
            safe_text = colored_text.encode('gbk', errors='replace').decode('gbk', errors='replace')
            print(safe_text, end=end, flush=flush)
        except Exception:
            ascii_text = ''.join(char if ord(char) < 128 else '?' for char in colored_text)
            print(ascii_text, end=end, flush=flush)


def print_welcome() -> None:
    """打印欢迎界面"""
    colored_print(f"{SYMBOLS['separator']}" * 70, 'separator_line')
    colored_print(
        f"    {SYMBOLS['star']} 我是制杖但勤劳的豆包AI "
        f"(支持上下文对话 + 深度思考控制) {SYMBOLS['star']}",
        'bright_white'
    )
    colored_print(f"{SYMBOLS['separator']}" * 70, 'separator_line')
    print()
    
    # ASCII艺术猫
    colored_print("      /\\_/\\    QUÉ MIRA BOBO?", 'cat_art')
    colored_print(" /\\  / o o \\    ﾉ", 'cat_art')
    colored_print("//\\\\ \\~(*)~/", 'cat_art')
    colored_print("`  \\/   ^ /", 'cat_art')
    colored_print("   | \\|| ||", 'cat_art')
    colored_print("   \\ '|| ||", 'cat_art')
    colored_print("    \\(()-())", 'cat_art')
    colored_print(" ~~~~~~~~~~~~~~~", 'cat_art')


def print_usage() -> None:
    """打印使用说明"""
    colored_print(f"{SYMBOLS['info']} 输入消息开始聊天", 'system_info')
    colored_print(f"{SYMBOLS['info']} 输入 'exit' 、'quit' 或 '退出' 关闭程序", 'system_info')
    colored_print(f"{SYMBOLS['info']} 输入 'clear'、'new' 或 '新话题' 开始新的聊天", 'system_info')
    colored_print(f"{SYMBOLS['info']} 深度思考控制：", 'system_info')
    colored_print("   - 默认：自动判断是否需要深度思考", 'system_info')
    colored_print("   - #think 开头：强制启用深度思考", 'system_info')
    colored_print("   - #fast 开头：禁用深度思考，快速回复", 'system_info')
    colored_print(f"{SYMBOLS['separator']}" * 70, 'separator_line')
    print()


def waiting_animation(stop_event: threading.Event) -> None:
    """显示等待动画
    
    Args:
        stop_event: 停止事件
    """
    spinners = SYMBOLS['spinner']
    messages = ["正在连接豆包AI...", "正在思考中...", "正在组织语言...", "马上就好..."]
    
    idx = 0
    msg_idx = 0
    msg_counter = 0
    
    while not stop_event.is_set():
        if msg_counter > 0 and msg_counter % 30 == 0:
            msg_idx = (msg_idx + 1) % len(messages)
        
        current_msg = f'{SYMBOLS["bot"]} 豆包: {spinners[idx]} {messages[msg_idx]}'
        if ENABLE_COLORS:
            colored_msg = f'{COLORS["bot_text"]}{current_msg}{COLORS["reset"]}'
        else:
            colored_msg = current_msg
        print(f'\r{colored_msg}' + ' ' * 20, end='', flush=True)
        
        idx = (idx + 1) % len(spinners)
        msg_counter += 1
        time.sleep(0.1)
    
    # 清除动画
    print('\r' + ' ' * 80, end='')
    if ENABLE_COLORS:
        colored_prefix = f'{COLORS["bot_text"]}{SYMBOLS["bot"]} 豆包: {COLORS["reset"]}'
    else:
        colored_prefix = f'{SYMBOLS["bot"]} 豆包: '
    print(f'\r{colored_prefix}', end='', flush=True)


class StreamOutputHandler:
    """流式输出处理器
    
    管理AI回复的流式输出显示。
    """
    
    def __init__(self):
        self.reasoning_displayed = False
        self.content_started = False
        self.first_chunk_received = False
        self.web_search_displayed = False
    
    def process_chunk(
        self,
        chunk_data: dict,
        stop_animation: threading.Event,
        thinking_status: str
    ) -> None:
        """处理单个chunk数据
        
        Args:
            chunk_data: chunk数据字典
            stop_animation: 停止动画事件
            thinking_status: 思考状态标记
        """
        if chunk_data is None:
            return
        
        chunk_type = chunk_data.get('type')
        
        # 处理Web Search事件
        if chunk_type == 'web_search_start':
            self._handle_web_search_start(stop_animation)
        elif chunk_type == 'web_search_searching':
            self._handle_web_search_searching(chunk_data)
        elif chunk_type == 'web_search_completed':
            self._handle_web_search_completed()
        
        # 处理深度思考内容
        elif chunk_type == 'reasoning' and chunk_data.get('reasoning'):
            self._handle_reasoning(chunk_data, stop_animation, thinking_status)
        
        # 处理普通回复内容
        elif chunk_type == 'content' and chunk_data.get('content'):
            self._handle_content(chunk_data, stop_animation, thinking_status)
    
    def _handle_web_search_start(self, stop_animation: threading.Event) -> None:
        """处理Web Search开始事件"""
        if not self.first_chunk_received:
            stop_animation.set()
            time.sleep(0.15)
            self.first_chunk_received = True
        if not self.web_search_displayed:
            colored_print(f"\n{SYMBOLS['connect']} 正在联网搜索...", 'system_info')
            self.web_search_displayed = True
    
    def _handle_web_search_searching(self, chunk_data: dict) -> None:
        """处理Web Search搜索中事件"""
        search_query = chunk_data.get('search_query', '')
        if search_query:
            colored_print(f"{SYMBOLS['arrow_right']} 搜索关键词: {search_query}", 'system_info')
    
    def _handle_web_search_completed(self) -> None:
        """处理Web Search完成事件"""
        colored_print(f"{SYMBOLS['success']} 联网搜索完成，正在整理答案...", 'system_success')
    
    def _handle_reasoning(
        self,
        chunk_data: dict,
        stop_animation: threading.Event,
        thinking_status: str
    ) -> None:
        """处理深度思考内容"""
        if not self.reasoning_displayed:
            if not self.first_chunk_received:
                stop_animation.set()
                time.sleep(0.15)
                self.first_chunk_received = True
            colored_print(f"\n{SYMBOLS['thinking']} 深度思考中...{thinking_status}", 'separator_line')
            colored_print(f"{SYMBOLS['star']} {SYMBOLS['separator'] * 46} {SYMBOLS['star']}", 'separator_line')
            self.reasoning_displayed = True
        colored_print(chunk_data['reasoning'], 'bot_thinking', end="", flush=True)
    
    def _handle_content(
        self,
        chunk_data: dict,
        stop_animation: threading.Event,
        thinking_status: str
    ) -> None:
        """处理普通回复内容"""
        if not self.content_started:
            if self.reasoning_displayed:
                colored_print(f"\n{SYMBOLS['star']} {SYMBOLS['separator'] * 46} {SYMBOLS['star']}", 'separator_line')
                if thinking_status != " [要求深度思考]":
                    colored_print(f"{SYMBOLS['bot']} 豆包{thinking_status}: ", 'bot_text', end="", flush=True)
            elif not self.first_chunk_received:
                stop_animation.set()
                time.sleep(0.15)
                self.first_chunk_received = True
            self.content_started = True
        
        if not self.first_chunk_received:
            stop_animation.set()
            time.sleep(0.15)
            self.first_chunk_received = True
        
        colored_print(chunk_data['content'], 'bot_text', end="", flush=True)
    
    def finalize(self, stop_animation: threading.Event) -> None:
        """完成输出处理"""
        if not self.first_chunk_received:
            stop_animation.set()
            time.sleep(0.15)
            print('\r' + ' ' * 80, end='')
            print('\r', end='', flush=True)
        
        if self.first_chunk_received:
            print()

