# 前端 自动修改 Agent

## 功能简介
- 命令行交互，自动修改前端项目
- 调用 AI 接口自动生成代码和任务
- 自动拆分任务并检查完成情况

## 使用方法
1. 安装依赖
   ```bash
   pip install -r requirements.txt
   # 或直接安装 dashscope
   pip install dashscope
   ```
2. 配置通义千问 API Key
   - 设置环境变量 `QWEN_API_KEY`，或在 `main.py` 中直接填写
3. 运行 agent
   ```bash
   python main.py
   ```
4. 按提示输入指令

## 依赖环境
- Python 3.8+
- Node.js
- npm

## 注意事项
- 支持所有前端项目
- 需联网以调用 OpenAI API
- 代码自动写入需人工确认
