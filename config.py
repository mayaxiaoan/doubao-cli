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