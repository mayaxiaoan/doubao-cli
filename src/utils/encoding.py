# -*- coding: utf-8 -*-
"""
编码处理工具模块

提供终端编码设置和相关工具函数。
"""

import sys
import os


def setup_encoding() -> bool:
    """设置终端编码为UTF-8
    
    Returns:
        设置是否成功
    """
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        return True
    except Exception:
        return False


def safe_decode(data: bytes, default_encoding: str = 'utf-8') -> str:
    """安全解码字节数据
    
    Args:
        data: 要解码的字节数据
        default_encoding: 默认编码
    
    Returns:
        解码后的字符串
    """
    try:
        return data.decode(default_encoding, errors='replace')
    except Exception:
        try:
            return data.decode('gbk', errors='replace')
        except Exception:
            return str(data)

