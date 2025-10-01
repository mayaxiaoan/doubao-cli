# -*- coding: utf-8 -*-
"""
豆包AI聊天程序配置文件
请在这里填写您的API密钥等信息
"""

import os

# 火山方舟API配置
# 方式1：直接在此处设置（不推荐，仅用于测试）
API_KEY = "13b58d60-5606-4d01-a0ba-2008b1316b0d"  # 请填写您的API密钥
ENDPOINT_ID = "ep-20250926160318-stwzh"  # 请填写您的接入点ID（格式：ep-xxxxx）

# 方式2：从环境变量读取（推荐）
# 您可以设置环境变量 ARK_API_KEY 和 ARK_ENDPOINT_ID
# 如果设置了环境变量，将优先使用环境变量的值
ARK_API_KEY = os.environ.get("ARK_API_KEY", API_KEY)
ARK_ENDPOINT_ID = os.environ.get("ARK_ENDPOINT_ID", ENDPOINT_ID)

# API基础URL（火山方舟官方URL）
API_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# 聊天参数配置
MAX_TOKENS = 2000  # 最大回复长度
TEMPERATURE = 0.7  # 回复的随机性，0-1之间，越高越随机
TOP_P = 0.9  # 核采样参数

# TTY/FBTERM兼容的精美颜文字符号配置
SYMBOLS = {
    # 状态相关 - 使用表情丰富的颜文字
    'success': '(◕‿◕)',       # ✅ 成功/完成 - 开心笑脸
    'error': '(╯︵╰)',        # ❌ 错误/失败 - 沮丧表情  
    'warning': '(￣□￣;)',     # ⚠️ 警告 - 困惑流汗
    'info': '(^•ﻌ•^)',         # 💡 提示/信息 - 友好提示
    'timeout': '(-_-)zzz',     # ⏰ 超时 - 睡觉等待
    
    # 角色相关 - 使用有趣的颜文字
    'bot': '(◉◡◉)',          # 🤖 机器人/AI - 可爱圆眼
    'user': '(^▽^)',         # 👤 用户 - 开心用户
    'thinking': '(・・?)',     # 💭 思考中 - 思考疑惑
    
    # 操作相关 - 使用动作表情
    'start': '╭( ･ㅂ･)و',     # 🚀 启动/开始 - 加油启动
    'connect': '⚡(^_^)',     # 🔗 连接/链接 - 闪电连接
    'celebrate': 'ヽ(^▽^)ﾉ', # 🎉 庆祝/启动成功 - 举手欢呼
    'goodbye': '(￣▽￣)ﾉ',    # 👋 再见/退出 - 挥手再见
    'docs': '(◕‿◕)✎',       # 📝 文档/记录 - 笑脸写字
    'list': '▸(・∀・)',       # 📋 列表/信息 - 箭头加笑脸
    'package': '◆(￣▽￣)',    # 📦 包/依赖 - 菱形加满意
    'folder': '◢(◕‿◕)',      # 📁 目录 - 三角加笑脸
    'python': '(=^･ω･^=)',    # 🐍 Python环境 - 可爱猫咪（代表灵活）
    'world': '(°▽°)',        # 🌍 环境 - 惊喜表情
    'end': '(￣▽￣)/',        # 🔚 结束 - 愉快结束
    
    # 动画字符（保持原有的盲文旋转效果，因为fbterm支持）
    'spinner': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
    
    # 新增：精选颜文字表情
    'happy': '(*≧▽≦)',       # 大笑开心
    'excited': 'ヽ(ﾟ▽ﾟ*)ノ',   # 兴奋激动
    'love': '(♥ω♥*)',        # 爱心眼
    'cool': '(⌐■_■)',        # 酷酷的
    'shy': '(〃ω〃)',         # 害羞脸红
    'surprised': '(⊙_⊙)',    # 惊讶圆眼
    'confused': '(￣～￣)',    # 困惑不解
    'sleepy': '(-_-) zzZ',    # 困倦睡觉
    'thumbs_up': '(b^_^)b',   # 双手点赞
    'peace': '(^-^)v',       # 比和平手势
    'hug': '(っ´▽｀)っ',       # 张开手臂拥抱
    'bow': 'm(_ _)m',         # 鞠躬道歉
    'shrug': '¯\\_(ツ)_/¯',   # 耸肩无奈
    'wink': '(^_－)☆',       # 眨眼
    'blush': '(⁄⁄•⁄ω⁄•⁄⁄)', # 害羞脸红
    
    # 装饰性符号
    'separator': '━',         # 分隔线
    'bullet': '•',           # 项目符号
    'arrow_right': '▶',      # 右箭头
    'arrow_left': '◀',       # 左箭头
    'heart': '♥',            # 爱心
    'star': '★',             # 实心星
    'star_empty': '☆',       # 空心星
    'music': '♪(๑ᴖ◡ᴖ๑)♪',   # 音乐表情
}

# FBTERM终端颜色配置 - 使用ANSI颜色代码
COLORS = {
    # 重置颜色
    'reset': '\033[0m',
    
    # 基础颜色 (30-37为前景色，90-97为亮色)
    'black': '\033[30m',
    'red': '\033[31m', 
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m',
    
    # 亮色版本
    'bright_black': '\033[90m',    # 灰色
    'bright_red': '\033[91m',
    'bright_green': '\033[92m',
    'bright_yellow': '\033[93m',
    'bright_blue': '\033[94m', 
    'bright_magenta': '\033[95m',
    'bright_cyan': '\033[96m',
    'bright_white': '\033[97m',
    
    # 文字样式
    'bold': '\033[1m',            # 粗体
    'dim': '\033[2m',             # 暗淡
    'italic': '\033[3m',          # 斜体
    'underline': '\033[4m',       # 下划线
    
    # 聊天内容颜色方案 - 适配fbterm的8色限制
    'user_text': '\033[32m',      # 绿色 - 用户输入
    'bot_text': '\033[37m',       # 白色 - 豆包回复（按用户要求）
    'bot_thinking': '\033[34m',   # 蓝色 - 豆包思考
    'system_info': '\033[36m',    # 青色 - 系统信息
    'system_success': '\033[36m', # 青色 - 成功消息
    'system_warning': '\033[33m', # 黄色/棕色 - 警告
    'system_error': '\033[31m',   # 红色 - 错误
    'separator_line': '\033[36m', # 青色 - 分隔线
    'cat_art': '\033[37m',        # 白色 - ASCII艺术猫（按用户要求）
}

# 是否启用颜色 (可以通过这个开关控制)
ENABLE_COLORS = True

# 深度思考默认模式配置
DEFAULT_THINKING_MODE = 'auto'  # 可选: 'auto', 'enabled', 'disabled'

# 全局规则配置 - 这些规则会应用到所有AI角色
GLOBAL_RULES = [
    "你是一位耐心的全能老师。向你提问的是初中和高中学生，你善于用他们浅显易懂的语言解释复杂概念，能循序渐进地帮助用户理解问题。（本括号内的内容是环境规则，你只需要按此规则执行，不要在聊天过程中提及：你是在tty终端运行，无法使用Emoji表情，所有表情请改为ASCII码颜文字，请使用简洁明了的语言回答问题，避免过于冗长的解释）"
]

# 是否启用全局规则
ENABLE_GLOBAL_RULES = True