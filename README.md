# Frontend Auto-modification Agent

## Function Introduction
- Command-line interaction, automatically modifies frontend projects
- Calls AI interface to automatically generate code and tasks
- Automatically splits tasks and checks completion status

## Usage
1. Install dependencies
   ```bash
   pip install -r requirements.txt
   # Or directly install dashscope
   pip install dashscope
   ```
2. Configure Qwen API Key
   - Set environment variable `QWEN_API_KEY`, or directly fill it in `main.py`
3. Run agent
   ```bash
   python main.py
   ```
4. Enter commands as prompted

## Dependencies
- Python 3.8+
- Node.js
- npm

## Notes
- Supports all frontend projects
- Requires internet connection to call OpenAI API
- Automatic code writing requires manual confirmation