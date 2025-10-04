# -*- coding: utf-8 -*-
"""
输入处理模块
处理用户输入，包括编码错误自动修复功能
"""

import sys
import platform

# Windows 下禁用 UTF8 修复功能（不需要）
_IS_WINDOWS = platform.system() == 'Windows'

# 只在非 Windows 系统导入 termios 和 tty
if not _IS_WINDOWS:
    try:
        import tty
        import termios
    except ImportError:
        _IS_WINDOWS = True

# 全局标志：记录是否已经显示过编码错误提示
_encoding_error_tip_shown = False


def getch():
    """读取单个按键（无需按Enter）"""
    if _IS_WINDOWS:
        raise NotImplementedError("getch not available on Windows")
    
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        # 检查是否是Esc键或特殊键序列
        if ch == '\x1b':  # Esc键
            # 尝试读取可能的后续字符（如方向键）
            sys.stdin.read(2)  # 清空可能的额外字符
            return 'esc'
        elif ch == '\r' or ch == '\n':  # Enter键
            return 'enter'
        else:
            return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _safe_input_windows(prompt_text):
    """Windows 下的简单输入（无需 UTF8 修复）"""
    try:
        user_input = input()
        return user_input.strip()
    except Exception:
        return ""


def _safe_input_linux(prompt_text, colored_print_func, symbols, colors, enable_colors):
    """Linux 下的输入（支持 UTF8 修复）"""
    global _encoding_error_tip_shown
    raw_input = None
    
    try:
        # 尝试从stdin.buffer读取原始字节
        if hasattr(sys.stdin, 'buffer'):
            raw_input = sys.stdin.buffer.readline()
            # 尝试解码
            user_input = raw_input.decode('utf-8').rstrip('\n\r')
            return user_input.strip()
        else:
            # 如果没有buffer属性，使用常规方式
            user_input = sys.stdin.readline().rstrip('\n\r')
            return user_input.strip()
            
    except UnicodeDecodeError as e:
        # 处理编码错误
        return _handle_encoding_error(
            e, raw_input, prompt_text, 
            colored_print_func, symbols, 
            colors, enable_colors
        )
        
    except Exception as e:
        print(f"\n{symbols['warning']} 输入处理错误: {e}")
        print(f"{symbols['info']} 请重新输入")
        return ""


def safe_input(prompt, colored_print_func, symbols, colors, enable_colors):
    """
    安全的输入函数，支持编码错误自动修复
    
    参数:
        prompt: 提示符文本
        colored_print_func: 彩色打印函数
        symbols: 符号字典
        colors: 颜色字典
        enable_colors: 是否启用颜色
    
    返回:
        用户输入的字符串（可能是修复后的）
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
        return _safe_input_windows(prompt)
    else:
        return _safe_input_linux(prompt, colored_print_func, symbols, colors, enable_colors)


def _handle_encoding_error(error, raw_input, prompt, colored_print_func, symbols, colors, enable_colors):
    """
    处理编码错误的内部函数
    
    参数:
        error: UnicodeDecodeError异常对象
        raw_input: 原始字节数据
        prompt: 提示符文本
        colored_print_func: 彩色打印函数
        symbols: 符号字典
        colors: 颜色字典
        enable_colors: 是否启用颜色
    
    返回:
        清理后的输入字符串或空字符串
    """
    global _encoding_error_tip_shown
    
    # 向上一行并清除
    print(f"\033[1A\033[2K", end="")
    
    # 尝试解码并清理输入
    displayed_input = None
    cleaned_input = None
    
    if raw_input:
        try:
            # 使用replace错误处理策略，用�替换无法解码的字符
            displayed_input = raw_input.decode('utf-8', errors='replace').rstrip('\n\r')
            # 创建清理后的版本，移除所有替换字符（�）
            cleaned_input = displayed_input.replace('\ufffd', '').strip()
        except:
            try:
                # 尝试GBK编码
                displayed_input = raw_input.decode('gbk', errors='replace').rstrip('\n\r')
                cleaned_input = displayed_input.replace('\ufffd', '').strip()
            except:
                displayed_input = None
                cleaned_input = None
    
    # 用红色重新显示提示符和用户输入
    if displayed_input:
        colored_print_func(f"{prompt}{displayed_input}", 'system_error')
    else:
        colored_print_func(f"{prompt}[编码错误，输入内容无法显示]", 'system_error')
    
    colored_print_func(f"{symbols['warning']} 输入编码错误: {error}", 'system_error')
    
    # 只在第一次显示详细提示
    if not _encoding_error_tip_shown:
        colored_print_func(
            f"{symbols['info']} 这可能是删除汉字导致的，由于编码显示的问题，"
            f"你每删除一个汉字实际要按三次回退键哦，记住次数，不要在意显示被删除的文字",
            'system_warning'
        )
        _encoding_error_tip_shown = True
    
    # 如果成功清理出有效内容，询问用户是否使用清理后的内容
    if cleaned_input:
        return _confirm_cleaned_input(cleaned_input, colored_print_func, symbols)
    
    return ""


def _confirm_cleaned_input(cleaned_input, colored_print_func, symbols):
    """
    询问用户是否使用清理后的内容
    
    参数:
        cleaned_input: 清理后的输入内容
        colored_print_func: 彩色打印函数
        symbols: 符号字典
    
    返回:
        如果用户确认则返回清理后的内容，否则返回空字符串
    """
    colored_print_func(f"{symbols['info']} 已自动清理错误字符，处理后的内容为:", 'system_info')
    colored_print_func(f"{symbols['user']} {cleaned_input}", 'bright_green')
    colored_print_func(f"{symbols['info']} 按 Enter 确认发送，按任意其他键取消并重新输入", 'system_info')
    
    try:
        key = getch()
        if key == 'enter':
            colored_print_func(f"{symbols['success']} 使用清理后的内容继续", 'system_success')
            return cleaned_input
        else:
            # 任意其他按键都视为取消
            colored_print_func(f"{symbols['info']} 已取消，请重新输入", 'system_info')
            return ""
    except Exception:
        # 如果getch失败，回退到传统方式
        colored_print_func(f"{symbols['info']} (输入 y 确认，其他键取消): ", 'system_info', end='', flush=True)
        try:
            choice = input().strip().lower()
            if choice in ['y', 'yes', '是', '']:
                colored_print_func(f"{symbols['success']} 使用清理后的内容继续", 'system_success')
                return cleaned_input
            else:
                colored_print_func(f"{symbols['info']} 已取消，请重新输入", 'system_info')
                return ""
        except:
            return ""


def reset_encoding_tip_flag():
    """重置编码错误提示标志（用于测试或重新开始会话）"""
    global _encoding_error_tip_shown
    _encoding_error_tip_shown = False

