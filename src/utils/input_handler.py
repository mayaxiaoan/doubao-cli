# -*- coding: utf-8 -*-
"""
输入处理模块

处理用户输入，支持编码错误自动修复。
"""

import sys
import platform
from typing import Callable, Dict, Optional

# Windows下禁用UTF8修复功能
_IS_WINDOWS = platform.system() == 'Windows'

# 只在非Windows系统导入termios和tty
if not _IS_WINDOWS:
    try:
        import tty
        import termios
    except ImportError:
        _IS_WINDOWS = True


class InputHandler:
    """输入处理器
    
    提供安全的用户输入功能，支持编码错误自动修复。
    """
    
    def __init__(self):
        self.encoding_error_tip_shown = False
    
    def get_input(
        self,
        prompt: str,
        print_func: Callable,
        symbols: Dict[str, str],
        colors: Dict[str, str],
        enable_colors: bool
    ) -> str:
        """获取用户输入
        
        Args:
            prompt: 提示符文本
            print_func: 彩色打印函数
            symbols: 符号字典
            colors: 颜色字典
            enable_colors: 是否启用颜色
        
        Returns:
            用户输入的字符串
        """
        # 生成彩色提示符
        if enable_colors and 'user_text' in colors:
            colored_prompt = f"{colors['user_text']}{prompt}{colors['reset']}"
        else:
            colored_prompt = prompt
        
        # 打印提示符
        print(colored_prompt, end='', flush=True)
        
        # 根据操作系统选择不同的实现
        if _IS_WINDOWS:
            return self._get_input_windows()
        else:
            return self._get_input_linux(
                prompt, print_func, symbols, colors, enable_colors
            )
    
    @staticmethod
    def _get_input_windows() -> str:
        """Windows下的输入处理"""
        try:
            user_input = input()
            return user_input.strip()
        except Exception:
            return ""
    
    def _get_input_linux(
        self,
        prompt: str,
        print_func: Callable,
        symbols: Dict[str, str],
        colors: Dict[str, str],
        enable_colors: bool
    ) -> str:
        """Linux下的输入处理（支持UTF8修复）"""
        try:
            # 尝试从stdin.buffer读取原始字节
            if hasattr(sys.stdin, 'buffer'):
                raw_input = sys.stdin.buffer.readline()
                user_input = raw_input.decode('utf-8').rstrip('\n\r')
                return user_input.strip()
            else:
                user_input = sys.stdin.readline().rstrip('\n\r')
                return user_input.strip()
        
        except UnicodeDecodeError as e:
            return self._handle_encoding_error(
                e, locals().get('raw_input'),
                prompt, print_func, symbols, colors, enable_colors
            )
        
        except Exception as e:
            print(f"\n{symbols['warning']} 输入处理错误: {e}")
            print(f"{symbols['info']} 请重新输入")
            return ""
    
    def _handle_encoding_error(
        self,
        error: UnicodeDecodeError,
        raw_input: Optional[bytes],
        prompt: str,
        print_func: Callable,
        symbols: Dict[str, str],
        colors: Dict[str, str],
        enable_colors: bool
    ) -> str:
        """处理编码错误"""
        # 向上一行并清除
        print(f"\033[1A\033[2K", end="")
        
        # 尝试解码并清理输入
        displayed_input = None
        cleaned_input = None
        
        if raw_input:
            try:
                displayed_input = raw_input.decode('utf-8', errors='replace').rstrip('\n\r')
                cleaned_input = displayed_input.replace('\ufffd', '').strip()
            except Exception:
                try:
                    displayed_input = raw_input.decode('gbk', errors='replace').rstrip('\n\r')
                    cleaned_input = displayed_input.replace('\ufffd', '').strip()
                except Exception:
                    pass
        
        # 显示错误信息
        if displayed_input:
            print_func(f"{prompt}{displayed_input}", 'system_error')
        else:
            print_func(f"{prompt}[编码错误，输入内容无法显示]", 'system_error')
        
        print_func(f"{symbols['warning']} 输入编码错误: {error}", 'system_error')
        
        # 只在第一次显示详细提示
        if not self.encoding_error_tip_shown:
            print_func(
                f"{symbols['info']} 这可能是删除汉字导致的，由于编码显示的问题，"
                f"你每删除一个汉字实际要按三次回退键哦，记住次数，不要在意显示被删除的文字",
                'system_warning'
            )
            self.encoding_error_tip_shown = True
        
        # 如果成功清理出有效内容，询问用户是否使用
        if cleaned_input:
            return self._confirm_cleaned_input(
                cleaned_input, print_func, symbols
            )
        
        return ""
    
    def _confirm_cleaned_input(
        self,
        cleaned_input: str,
        print_func: Callable,
        symbols: Dict[str, str]
    ) -> str:
        """询问用户是否使用清理后的内容"""
        print_func(f"{symbols['info']} 已自动清理错误字符，处理后的内容为:", 'system_info')
        print_func(f"{symbols['user']} {cleaned_input}", 'bright_green')
        print_func(f"{symbols['info']} 按 Enter 确认发送，按任意其他键取消并重新输入", 'system_info')
        
        try:
            key = self._getch()
            if key == 'enter':
                print_func(f"{symbols['success']} 使用清理后的内容继续", 'system_success')
                return cleaned_input
            else:
                print_func(f"{symbols['info']} 已取消，请重新输入", 'system_info')
                return ""
        except Exception:
            # 如果getch失败，回退到传统方式
            print_func(f"{symbols['info']} (输入 y 确认，其他键取消): ", 'system_info', end='', flush=True)
            try:
                choice = input().strip().lower()
                if choice in ['y', 'yes', '是', '']:
                    print_func(f"{symbols['success']} 使用清理后的内容继续", 'system_success')
                    return cleaned_input
                else:
                    print_func(f"{symbols['info']} 已取消，请重新输入", 'system_info')
                    return ""
            except Exception:
                return ""
    
    @staticmethod
    def _getch() -> str:
        """读取单个按键"""
        if _IS_WINDOWS:
            raise NotImplementedError("getch not available on Windows")
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            
            if ch == '\x1b':  # Esc键
                sys.stdin.read(2)
                return 'esc'
            elif ch in ('\r', '\n'):  # Enter键
                return 'enter'
            else:
                return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def reset_tip_flag(self) -> None:
        """重置编码错误提示标志"""
        self.encoding_error_tip_shown = False

