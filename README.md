# 前端自动修改 Agent

## 功能简介
- 命令行交互，自动修改前端项目
- 调用 AI 接口自动生成代码和任务
- 自动拆分任务并检查完成情况

## 使用方法
1. 安装依赖
   ```bash
   pip install -r requirements.txt
   # 或直接安装 dashscope
   pip install dashscope prompt_toolkit
   ```
2. 配置通义千问 API Key
   - 设置环境变量 `DASHSCOPE_API_KEY`，或在运行时按提示输入
3. 运行 agent
   ```bash
   python main.py
   ```
4. 按提示输入指令

## 依赖环境
- Python 3.8+
- Node.js
- npm

## 项目结构
```
.
├── agents/               # 核心应用模块
│   ├── __init__.py
│   └── application.py    # 主应用类
├── commands/             # 命令处理模块
│   ├── __init__.py
│   ├── ai_commands.py    # AI相关命令处理
│   └── project_commands.py # 项目相关命令处理
├── services/             # 业务服务模块
│   ├── __init__.py
│   ├── ai_interactor.py  # AI交互服务
│   ├── config.py         # 配置管理服务
│   ├── file_operator.py  # 文件操作服务
│   └── project_analyzer.py # 项目分析服务
├── exceptions/           # 自定义异常模块
│   ├── __init__.py
│   └── project_exceptions.py
├── utils/                # 工具模块
│   ├── __init__.py
│   └── helpers.py
├── main.py               # 主程序入口
├── requirements.txt      # 依赖列表
└── README.md             # 说明文档
```

## 核心功能

### 1. 项目分析
自动分析前端项目结构，识别关键文件和目录。

### 2. AI辅助开发
通过ReAct模式与AI交互，生成高质量的代码修改建议。

### 3. 安全的文件操作
所有文件操作都会进行路径验证和自动备份，防止意外修改。

### 4. 项目运行管理
支持一键安装依赖和运行项目。

## 配置说明

### 环境变量
- `DASHSCOPE_API_KEY`: 通义千问API密钥（必需）

### 配置项
- `model_name`: 使用的AI模型名称，默认为`qwen3-coder-plus`
- `max_retries`: API调用最大重试次数，默认为3次
- `timeout`: API调用超时时间，默认为30秒

## 安全特性
- 所有文件路径都经过验证，防止路径遍历攻击
- 文件修改前会自动创建备份
- 敏感操作需要用户确认

## 注意事项
- 支持所有前端项目
- 需联网以调用AI API
- 代码自动写入需人工确认
- 项目会在修改文件后自动重新分析项目结构

## 故障排除

### API密钥问题
确保已正确设置`DASHSCOPE_API_KEY`环境变量。

### 依赖安装问题
确保Node.js和npm已正确安装并添加到系统PATH中。

### 文件修改问题
如果AI生成的代码不符合预期，可以拒绝应用修改，系统会自动清理相关历史记录。