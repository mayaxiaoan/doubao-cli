# 豆包AI聊天程序 (官方SDK版本)

一个基于火山引擎官方Python SDK的豆包AI聊天程序，使用火山方舟大模型平台API。

## 功能特性

- 🤖 与豆包AI进行自然对话
- ⚡ 使用火山引擎官方SDK，稳定可靠
- 🔐 支持环境变量配置，安全便捷
- 🔧 基于火山方舟API平台

## 项目结构

```
PyDoubao/
├── config.py           # API配置文件
├── doubao_client.py    # 豆包客户端类（官方SDK）
├── main.py            # 主程序
├── requirements.txt   # 依赖包
├── setup_guide.txt    # 配置指南
└── README.md         # 说明文档
```

## 使用步骤

### 1. 安装依赖

```bash
pip install volcengine
```

或者使用 requirements.txt：

```bash
pip install -r requirements.txt
```

### 2. 获取API密钥和接入点ID

1. 访问 [火山引擎控制台](https://console.volcengine.com/ark)
2. 注册账号并完成实名认证  
3. 在"API密钥管理"中创建API密钥
4. 在"推理接入点"页面创建豆包模型接入点，获取接入点ID

### 3. 配置API信息

#### 方式1：修改配置文件（简单）

编辑 `config.py` 文件：

```python
API_KEY = "your_actual_api_key"           # 填写您的真实API密钥
ENDPOINT_ID = "ep-your-endpoint-id"       # 填写您的真实接入点ID
```

#### 方式2：设置环境变量（推荐）

设置环境变量：

```bash
# Windows
set ARK_API_KEY=your_actual_api_key
set ARK_ENDPOINT_ID=ep-your-endpoint-id

# Linux/Mac
export ARK_API_KEY=your_actual_api_key
export ARK_ENDPOINT_ID=ep-your-endpoint-id
```

### 4. 运行程序

```bash
python main.py
```

## 使用示例

```
==================================================
🤖 豆包AI聊天程序
==================================================
💡 输入消息开始聊天，输入 'exit' 或 'quit' 退出程序
==================================================
✅ 豆包AI客户端初始化成功
✅ 使用接入点: ep-20250926160318-stwzh

👤 您: 你好，豆包！
🤖 豆包: 你好！我是豆包，很高兴为您服务。有什么我可以帮助您的吗？

👤 您: exit
👋 感谢使用豆包AI聊天程序，再见！
```

## API配置说明

### 配置文件说明

`config.py` 中的主要配置项：

- `API_KEY`: 火山方舟API密钥
- `ENDPOINT_ID`: 模型接入点ID（格式：ep-xxxxx）
- `ARK_API_KEY`: 从环境变量读取的API密钥（优先级更高）
- `ARK_ENDPOINT_ID`: 从环境变量读取的接入点ID（优先级更高）
- `API_BASE_URL`: API基础URL
- `MAX_TOKENS`: 最大回复长度
- `TEMPERATURE`: 随机性参数 (0-1)
- `TOP_P`: 核采样参数

### 正确的配置格式

- **API密钥**: 从火山引擎控制台获取的完整API密钥
- **接入点ID**: 格式为 `ep-` 开头的字符串，例如：`ep-20250926160318-stwzh`

## 技术架构

- **官方SDK**: 使用 `volcenginesdkarkruntime.Ark` 客户端
- **API调用**: 通过 `client.chat.completions.create()` 方法
- **加密传输**: 启用应用层加密 `x-is-encrypted: true`
- **错误处理**: 完整的异常处理和错误信息显示

## 故障排除

### 常见错误

1. **配置错误**: 
   ```
   ValueError: 请在config.py中设置有效的API_KEY或设置环境变量ARK_API_KEY
   ```
   **解决方法**: 检查API密钥配置是否正确

2. **接入点错误**: 
   ```
   ValueError: 请在config.py中设置有效的ENDPOINT_ID或设置环境变量ARK_ENDPOINT_ID
   ```
   **解决方法**: 检查接入点ID格式是否为 `ep-xxxxx`

3. **SDK导入错误**:
   ```
   ModuleNotFoundError: No module named 'volcenginesdkarkruntime'
   ```
   **解决方法**: 运行 `pip install volcengine`

### 调试提示

程序会显示详细的错误信息，包括：
- 初始化状态
- 使用的接入点ID
- API调用异常详情
- 完整的错误堆栈信息

## 环境变量配置

为了安全起见，推荐使用环境变量配置：

```bash
# 设置API密钥
export ARK_API_KEY="your_api_key_here"

# 设置接入点ID  
export ARK_ENDPOINT_ID="ep-your-endpoint-id"
```

## 系统要求

- Python 3.6+
- volcengine SDK (>=1.0.201)
- 有效的火山方舟API密钥和接入点ID

## 更新日志

- **v2.0**: 使用火山引擎官方SDK
- **v1.0**: 基于requests库的简单实现

## 许可证

本项目仅供学习和个人使用。